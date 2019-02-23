import sys
import os
import logging
import subprocess
import shutil
import sqlite3
import csv
import codesigning_common

# The list of patforms must be same as valid platforms in QDK
# refer to file "qbuild" at https://github.com/qnap-dev/QDK/
PLATFORMS=["arm-x09","arm-x19","arm-x31","arm-x41","arm_64","x86","x86_ce53xx","x86_64"]

def check_qpkg_conf(kwargs):
    # Check if qpkg.cfg exists, and read paramaters from it

    qpkg_conf = os.path.join(kwargs["cwd"],"qpkg.cfg")
    if not os.path.isfile(qpkg_conf):
        logging.error("Cannot find qpkg.cfg")
        sys.exit(codesigning_common.CONF_ERROR)
    commands = ["source %s" % qpkg_conf, "echo $QPKG_NAME"]
    sp = subprocess.Popen("bash",stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for cmd in commands:
        sp.stdin.write(cmd + "\n")
    sp.stdin.close()
    kwargs["qpkgname"] = sp.stdout.read().strip()

    commands = ["source %s" % qpkg_conf, "echo $QPKG_VER"]
    sp = subprocess.Popen("bash",stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for cmd in commands:
        sp.stdin.write(cmd + "\n")
    sp.stdin.close()
    kwargs["version"] = sp.stdout.read().strip()

    if kwargs["qpkgname"] == "":
        logging.error("Cannot find QPKG_NAME in qpkg.cfg")
        sys.exit(codesigning_common.CONF_ERROR)
    if kwargs["version"] == "":
        logging.error("Cannot find QPKG_VER in qpkg.cfg")
        sys.exit(codesigning_common.CONF_ERROR)

def create_dbs(kwargs):
    for platform in PLATFORMS:
        platform_folder = os.path.join(kwargs["cwd"],platform)
        if os.path.isdir(platform_folder):
            codesigning_folder = os.path.join(platform_folder,".qcodesigning")
            codesigning_common.create_db(codesigning_folder + "/" + codesigning_common.DB_NAME)
            kwargs["codesigning_folders"].append(codesigning_folder)
    if len(kwargs["codesigning_folders"]) == 0: # no platform folder, use shared folder
        shared_folder = os.path.join(kwargs["cwd"],"shared")
        if not os.path.isdir(shared_folder):
            logging.error("Cannot find shared folder")
            sys.exit(codesigning_common.FOLDER_ERROR)
        codesigning_folder = shared_folder + "/.qcodesigning"
        codesigning_common.create_db(codesigning_folder + "/" + codesigning_common.DB_NAME)
        kwargs["codesigning_folders"].append(codesigning_folder)

def get_first_dir(relative_path):
    dirname = os.path.dirname(relative_path)
    while os.path.dirname(dirname) != "":
        dirname = os.path.dirname(dirname)
    if dirname not in PLATFORMS and dirname != "shared":
        logging.warning("Invalid relative path in csv: %s" % relative_path)
        return None
    elif not os.path.isdir(os.path.join(kwargs["cwd"],dirname)):
        logging.warning("Cannot find folder: %s" % dirname)
        return None
    return dirname

def get_dbs_by_first_dir(kwargs, first_dir):
    if first_dir == "shared":
        return list(folder + "/" + codesigning_common.DB_NAME for folder in kwargs["codesigning_folders"])
    for foldername in kwargs["codesigning_folders"]:
        platform = os.path.basename(os.path.dirname(foldername))
        if first_dir == platform:
            ret = []
            ret.append(foldername + "/" + codesigning_common.DB_NAME)
            return ret
    logging.error("Unrecognized folder: %s" % first_dir)
    sys.exit(codesigning_common.FOLDER_ERROR)

def update_dbs_by_csv(kwargs):
    # Get paths,packages from csv and insert/update DB
    sql_insert_path = "INSERT INTO SignedFile (Path, Package) VALUES (?, ?);"
    conns = {}
    rows = codesigning_common.read_csv(kwargs["csv"])
    for row in rows:
        package = row[0]
        relative_path = row[1]
        absolute_path = row[2]
        first_dir = get_first_dir(relative_path)
        if first_dir == None:
            continue
        dbs = get_dbs_by_first_dir(kwargs, first_dir)
        for db in dbs:
            if db not in conns:
                conns[db] = sqlite3.connect(db)
                conn = conns[db]
            else:
                conn = conns[db]
            cur = conn.cursor()
            cur.execute(sql_insert_path, (absolute_path, package))
    for db in conns:
        conn = conns[db]
        conn.commit()
        conn.close()
        logging.info("Paths and Packages from csv updated to codesigning DB %s" % db)

def create_tgzs(kwargs):
    # Copy files into temp_folder and then create tgzs

    # Check if temporary folder or tgz file exists already
    tar_list = []
    for folder in kwargs["codesigning_folders"]:
        temp_folder = folder + "/tgz"
        output_tgz_file = temp_folder + ".tgz"
        codesigning_common.check_for_tgz(temp_folder,output_tgz_file)
        tar_list.append({"folder":temp_folder,"target":output_tgz_file})

    rows = codesigning_common.read_csv(kwargs["csv"])
    # Copy files into temp folders
    for row in rows:
        relative_path = row[1]
        absolute_path = row[2]
        src = os.path.join(kwargs["cwd"], relative_path)
        if not os.path.isfile(src):
            logging.warning("Cannot find file " + relative_path)
            continue
        platform = get_first_dir(relative_path)
        if platform == None:
            continue
        if platform == "shared":
            for folder in kwargs["codesigning_folders"]:
                temp_folder = folder + "/tgz"
                dst = temp_folder + absolute_path
                codesigning_common.copy_file(src, dst)
        else:
            temp_folder = os.path.join(kwargs["cwd"],platform) + "/.qcodesigning/tgz"
            dst = temp_folder + absolute_path
            codesigning_common.copy_file(src, dst)
    for tar_task in tar_list:
        codesigning_common.create_tgz(tar_task["folder"],tar_task["target"])

def sign_and_update_signature(kwargs):
    # Send tar files to server, and then update signatures to DBs
    for folder in kwargs["codesigning_folders"]:
       kwargs["tgzfile"] = folder + "/tgz.tgz"
       server_response = codesigning_common.sign_files(kwargs)
       kwargs["db"] = folder + "/" + codesigning_common.DB_NAME
       codesigning_common.update_signatures(kwargs, server_response)
       os.remove(kwargs["tgzfile"])

def save_certificate(kwargs):
    for folder in kwargs["codesigning_folders"]:
        pem_file_name = folder + "/" + codesigning_common.CERT_NAME
        db = folder + "/" + codesigning_common.DB_NAME
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        sql = "SELECT Cert FROM Certificate LIMIT 1;"
        cur.execute(sql)
        entry = cur.fetchone()
        pem = entry[0]
        pem_file = open(pem_file_name, "w")
        pem_file.write(pem)
        pem_file.close()

def sign_and_save_db_signatures(kwargs):
    for folder in kwargs["codesigning_folders"]:
        # Generate tgz
        temp_folder = folder + "/db"
        output_tgz_file = temp_folder + ".tgz"
        codesigning_common.check_for_tgz(temp_folder,output_tgz_file)
        db_file = folder + "/" + codesigning_common.DB_NAME
        shutil.copyfile(db_file, temp_folder + "/" + os.path.basename(db_file))
        codesigning_common.create_tgz(temp_folder, output_tgz_file)

        # Send to server
        kwargs["tgzfile"] = output_tgz_file
        response = codesigning_common.sign_files(kwargs)
        if response["error"] != 0:
            logging.error("Error message from server when signing codesigning DB: %s" % response["msg"])
            logging.error("DB at %s" % db_file)
            sys.exit(codesigning_common.SERVER_ERROR)
        os.remove(output_tgz_file)
        signature_b64 = response["signatures"][0]["signature"]
        signature = codesigning_common.b64_decode(signature_b64)

        # Save to file
        signature_file_name = folder + "/" + codesigning_common.DB_SIG_NAME
        signature_file = open(signature_file_name, "w+b")
        signature_file.write(signature)
        signature_file.close()

def print_usage():
    usage_string = """
    Usage:
        python codesigning-qdk.py server=x.x.x.x:port cwd=working_directory csv=csv_file.csv
        cert=certificate.pem
        working directory: the folder where QDK developers run qbuild
        cert: certificate of code signing server (optional)
    """
    print (usage_string)

if __name__ == "__main__":
    # Config logging
    codesigning_common.config_logging()

    try:
        kwargs = dict(arg.split('=') for arg in sys.argv[1:])
    except:
        print_usage()
        sys.exit(1)
    if "server" not in kwargs or "cwd" not in kwargs or \
            "csv" not in kwargs or (len(kwargs) != 3 and len(kwargs) != 4):
        print_usage()
        sys.exit(1)
    codesigning_common.check_args(kwargs)
    kwargs["token"] = codesigning_common.get_token()
    kwargs["key_type"] = "qpkg"
    codesigning_common.check_cwd(kwargs)
    kwargs["codesigning_folders"] = []
    check_qpkg_conf(kwargs)
    create_dbs(kwargs)
    update_dbs_by_csv(kwargs)
    create_tgzs(kwargs)
    sign_and_update_signature(kwargs)
    save_certificate(kwargs)
    sign_and_save_db_signatures(kwargs)
