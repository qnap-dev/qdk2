#!/usr/bin/env python2

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     realpath as prealpath,
                     basename as pbasename,
                     )
from os import makedirs, chmod, chdir, getcwd, symlink, listdir
from shutil import copy, rmtree, copytree, move
# import hashlib
import subprocess
import os
from contextlib import contextmanager
from collections import defaultdict

from basecommand import BaseCommand
from log import info, error, debug
# from lint import CommandLint
from controlfiles import ControlFile, ChangelogFile
from settings import Settings
from exception import (PackageNotFound, FileSyntaxError, BaseStringException,
                       BuildingError)


class QbuildToQpkg(object):
    def __init__(self, path):
        self._path = path

    def build(self):
        cwd = getcwd()
        chdir(self._path)
        try:
            cmd = [pjoin(cwd, Settings.QBUILD)]
            if Settings.DEBUG:
                cmd.append('--verbose')
            else:
                cmd.append('-q')
            debug(cmd)
            subprocess.check_call(cmd)
        finally:
            chdir(cwd)
        for fname in listdir(pjoin(self._path, 'build')):
            if fname.endswith('.qpkg'):
                return pjoin(self._path, 'build', fname)
        raise BuildingError('No *.qpkg found in ' + pjoin(self._path, 'build'))


class Qdk2ToQbuild(object):
    def __init__(self, data):
        self.build_dir = data.build_dir
        self.qpkg_dir = data.qpkg_dir

    def transform(self):
        cfile = ControlFile()
        result = []
        with self._setup_all(cfile):
            for k in cfile.packages:
                result.append(self._transform_one(cfile.packages[k]))
        return result

    def build_env(self, package):
        cfile = ControlFile()
        if package not in cfile.packages:
            raise PackageNotFound(package)
        with self._setup_all(cfile), self._setup(cfile.packages[package]):
            env = self._env.copy()
            return env

    @contextmanager
    def _setup_all(self, control):
        cwd = getcwd()
        dest = prealpath(pjoin(self.build_dir, control.source['source']))
        if pexists(dest):
            rmtree(dest)
        if not pexists(self.build_dir):
            makedirs(self.build_dir)
        # if dest in qpkg_dir
        copytree(self.qpkg_dir, dest)
        self.source = control.source
        chdir(dest)

        yield None

        chdir(cwd)
        del self.source

    def _transform_one(self, package):
        with self._setup(package):
            self._build()
            self._binary()
            self._cook_install()
            self._cook_dirs()
            self._cook_links()
            self._copy_controls()
            self._copy_icons()
            self._cook_package_routines()
            self._cook_init_sh()
            self._cook_qpkg_cfg()
            self._cook_conffiles()
            self._cook_list()
            self._cook_signature()
            self._cook_md5sum()
            return self._env['QPKG_DEST_CONTROL']

    @contextmanager
    def _setup(self, package):
        def prepare_dest():
            dest = prealpath(pjoin(
                '.', Settings.CONTROL_PATH,
                package['package'] + '_' + package['architecture']))
            if pexists(dest):
                rmtree(dest)
            self._env['QPKG_DEST'] = pjoin(dest, 'shared')
            self._env['QPKG_DEST_DATA'] = self._env['QPKG_DEST']
            self._env['QPKG_DEST_CONTROL'] = dest
            makedirs(self._env['QPKG_DEST'])

        def prepare_env():
            myenv = os.environ.copy()
            for k, v in self.package.iteritems():
                myenv['QPKG_' + k.upper().replace('-', '_')] = v
            for k, v in self.source.iteritems():
                myenv['QPKG_' + k.upper().replace('-', '_')] = v
            myenv['QPKG_VERSION'] = ChangelogFile().version
            if pexists(pjoin(Settings.CONTROL_PATH,
                             package['package'] + '.init')):
                myenv['QPKG_INIT'] = package['package'] + '.init'
            self._env = myenv

        self.package = package
        prepare_env()
        prepare_dest()
        yield None
        del self._env
        del self.package

    def _build(self):
        try:
            subprocess.check_call([pjoin(Settings.CONTROL_PATH, 'rules'),
                                   'build',
                                   ], env=self._env)
        except subprocess.CalledProcessError as e:
            raise e

    def _binary(self):
        try:
            subprocess.check_call([pjoin(Settings.CONTROL_PATH, 'rules'),
                                   'binary',
                                   ], env=self._env)
        except subprocess.CalledProcessError as e:
            raise e

    def _cook_install(self):
        src_install = pjoin(Settings.CONTROL_PATH,
                            self.package['package'] + '.install')
        if not pexists(src_install):
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    src, dst = line.strip().split(' ', 1)
                    if not pexists(src):
                        raise FileSyntaxError(src_install,
                                              lineno, src + ' not found')
                    if dst.startswith('/'):
                        dst = '.' + dst
                    dst = pjoin(self._env['QPKG_DEST'], dst)
                    if not pexists(dst):
                        makedirs(dst)
                    copy(src, dst)
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    def _cook_links(self):
        src_install = pjoin(Settings.CONTROL_PATH,
                            self.package['package'] + '.links')
        if not pexists(src_install):
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    src, dst = line.strip().split(' ', 1)
                    if dst.startswith('/'):
                        dst = '.' + dst
                    dst = pjoin(self._env['QPKG_DEST'], dst)
                    if dst.endswith('/'):
                        if not pexists(dst):
                            makedirs(dst)
                        dst = pjoin(dst, pbasename(src))
                    symlink(src, dst)
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    def _cook_dirs(self):
        src_install = pjoin(Settings.CONTROL_PATH,
                            self.package['package'] + '.dirs')
        if not pexists(src_install):
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    dst = pjoin(self._env['QPKG_DEST'], line.strip())
                    if not pexists(dst):
                        makedirs(dst)
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    def _copy_controls(self):
        package = self.package
        replace_mapping = [('%' + k + '%', v) for k, v in self._env.iteritems()
                           if k.startswith('QPKG_')]
        suffix_all = ['.conffiles', '.postrm', '.prerm', '.postinst',
                      '.preinst', '.mime', '.service', '.init']
        suffix_to_fixperm = ['.postrm', '.prerm', '.postinst', '.preinst']
        dest_base = pjoin(self._env['QPKG_DEST_DATA'], '.qdk2')
        makedirs(dest_base)
        for suffix in suffix_all:
            src = pjoin(Settings.CONTROL_PATH, package['package'] + suffix)
            dest = pjoin(dest_base, package['package'] + suffix)
            if suffix in ('.init',):
                dest = pjoin(self._env['QPKG_DEST_CONTROL'],
                             package['package'] + suffix)
            if not pexists(src):
                continue
            with open(src, 'r') as fin, open(dest, 'w+') as fout:
                for line in fin:
                    for k, v in replace_mapping:
                        line = line.replace(k, v)
                    fout.write(line)
            # fix perm
            if suffix in suffix_to_fixperm:
                chmod(dest, 0555)

    def _copy_icons(self):
        dest_base = pjoin(self._env['QPKG_DEST_CONTROL'], 'icons')
        makedirs(dest_base)
        package_name = self.package['package']
        icons = (('.icon.64', '.gif'), ('.icon.80', '_80.gif'),
                 ('.icon.gray', '_gray.gif'),
                 )
        for suffix, rsuffix in icons:
            src = pjoin(Settings.CONTROL_PATH, package_name + suffix)
            dest = pjoin(dest_base, package_name + rsuffix)
            if not pexists(src):
                continue
            copy(src, dest)

    def _cook_package_routines(self):
        # TODO postrm would not be executed because the file already was removed
        path = self._env['QPKG_PACKAGE']

        content = (
            r'PKG_PRE_REMOVE="{',
            r'echo 3s >> /tmp/p.txt',
            r'QPKG_INIT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.service',
            r'if [ -f ${QPKG_INIT} ]; then ',
            r'    rm -f /etc/config/systemd/system/' + path + r'.service',
            r'fi',
            r'SCRIPT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.prerm',
            r'[ -x \${SCRIPT} ] && \${SCRIPT} remove',
            r'echo 3e >> /tmp/p.txt',
            r'}"',
            r'',
            r'PKG_MAIN_REMOVE="{',
            r'true',
            r'}"',
            r'',
            r'PKG_POST_REMOVE="{',
            r'echo 4s >> /tmp/p.txt',
            r'SCRIPT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.postrm',
            r'[ -x \${SCRIPT} ] && \${SCRIPT} remove',
            r'echo 4e >> /tmp/p.txt',
            r'}"',
            r'',
            r'pkg_init(){',
            r'true',
            r'}',
            r'',
            r'pkg_check_requirement(){',
            r'true',
            r'}',
            r'',
            r'pkg_pre_install(){',
            r'echo 1s > /tmp/p.txt',
            r'SCRIPT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.preinst',
            r'[ -x ${SCRIPT} ] && ${SCRIPT} install',
            r'echo 1e >> /tmp/p.txt',
            r'}',
            r'',
            r'pkg_install(){',
            r'true',
            r'}',
            r'',
            r'pkg_post_install(){',
            r'echo 2s >> /tmp/p.txt',
            r'QPKG_INIT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.service',
            r'if [ -f ${QPKG_INIT} ]; then ',
            r'    ln -s "$QPKG_INIT" /etc/config/systemd/system/',
            r'fi',
            r'SCRIPT=${SYS_QPKG_DIR}/.qdk2/' + path + r'.postinst',
            r'[ -x ${SCRIPT} ] && ${SCRIPT} configure',
            r'echo 2e >> /tmp/p.txt',
            r'}',
        )

        with open(pjoin(self._env['QPKG_DEST_CONTROL'],
                        'package_routines'), 'w+') as f:
            f.write('\n'.join(content))

    def _cook_qpkg_cfg(self):
        content = (
            r'QPKG_NAME="{0[QPKG_PACKAGE]}"',
            r'QPKG_DISPLAYNAME="{0[QPKG_Q_APPNAME]}"',
            r'QPKG_VER="{0[QPKG_VERSION]}"',
            r'QPKG_AUTHOR="{0[QPKG_MAINTAINER]}"',
            r'QPKG_LICENSE="{0[QPKG_LICENSE]}"',
            r'#QPKG_SUMMARY=""',
            r'QPKG_RC_NUM="101"',
            r'QPKG_SERVICE_PROGRAM="{0[QPKG_INIT]}"',
            r'#QPKG_REQUIRE="Python >= 2.7, Optware | opkg, OPT/openssh"',
            r'#QPKG_CONFLICT="Python, OPT/sed"',
            r'#QPKG_CONFIG="myApp.conf"',
            r'#QPKG_CONFIG="/etc/config/myApp.conf"',
            r'QPKG_SERVICE_PORT="{0[QPKG_Q_SERVICE_PORT]}"',
            r'#QPKG_SERVICE_PIDFILE=""',
            r'QPKG_WEBUI="{0[QPKG_Q_WEBUI]}"',
            r'QPKG_WEB_PORT="{0[QPKG_Q_WEB_PORT]}"',
            r'#QDK_DATA_DIR_ICONS="icons"',
        )

        env = defaultdict(str)
        for k, v in self._env.iteritems():
            if k.startswith('QPKG_'):
                env[k] = v
        with open(pjoin(self._env['QPKG_DEST_CONTROL'],
                        'qpkg.cfg'), 'w+') as f:
            f.write(('\n'.join(content)).format(env))

    def _cook_init_sh(self):
        init = pjoin(self._env['QPKG_DEST_CONTROL'],
                     self.package['package'] + '.init')
        if pexists(init):
            copy(init, self._env['QPKG_DEST_DATA'])
            move(pjoin(self._env['QPKG_DEST_DATA'], pbasename(init)),
                 pjoin(self._env['QPKG_DEST_DATA'], self._env['QPKG_INIT']))
            chmod(pjoin(self._env['QPKG_DEST_DATA'], self._env['QPKG_INIT']),
                  0555)

    def _cook_conffiles(self):
        # conffiles
        pass

    def _cook_list(self):
        # list
        #   links
        #   dirs
        pass

    def _cook_signature(self):
        # TODO: add gpg
        with open(pjoin(self._env['QPKG_DEST_CONTROL'], 'qpkg-version'), 'w') as f:
            f.write(Settings.QPKG_VERSION)
        pass

    def _cook_md5sum(self):
        # md5sum
        # hashlib.md5(
        # open("/tmp/lp-fish-tools_1.22.1.tar.gz").read()).hexdigest()
        pass


class CommandBuild(BaseCommand):
    key = 'build'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='build QPKG')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('--qpkg-dir',
                            default='./',
                            help='Source package')
        parser.add_argument('--build-dir',
                            default='../build-area',
                            help='Folder to store building stuff')
        parser.add_argument('--build-env',
                            default=None,
                            help='List build environment')
        parser.add_argument('--as-qdk1', action='store_true',
                            default=False,
                            help='Source package is QDK 1 format')

    @property
    def qpkg_dir(self):
        if not hasattr(self, '_qpkg_dir'):
            self._qpkg_dir = self._args.qpkg_dir
        return self._qpkg_dir

    @property
    def build_dir(self):
        if not hasattr(self, '_build_dir'):
            self._build_dir = self._args.build_dir
        return self._build_dir

    def run(self, **kargs):
        for k in kargs:
            setattr(self, '_' + k, kargs[k])

        if self._args.build_env is not None:
            try:
                env = Qdk2ToQbuild(self).build_env(self._args.build_env)
                for k in sorted(env.iterkeys()):
                    print "%s=%s" % (k, env[k])
            except PackageNotFound:
                error('No package ' + self._args.build_env)
            return 0

        if self._args.as_qdk1:
            q = self._args.qpkg_dir
            result = QbuildToQpkg(q).build()
            arch = '_i386'  # TODO
            dest = pjoin(self.build_dir,
                         pbasename(result)[:-5] + arch + '.qpkg')
            move(result, dest)
            info('Package is ready: ' + dest)
            return 0

        try:
            qbuild_formats = Qdk2ToQbuild(self).transform()
            for q in qbuild_formats:
                debug(q)
                result = QbuildToQpkg(q).build()
                arch = q[q.rfind('_'):]
                dest = pjoin(self.build_dir,
                             pbasename(result)[:-5] + arch + '.qpkg')
                move(result, dest)
                info('Package is ready: ' + dest)
        except BaseStringException as e:
            error(str(e))
            return -1

        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
