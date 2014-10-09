#!/usr/bin/env python

from os import symlink, makedirs, chmod, walk, unlink
from os.path import (exists as pexists,
                     join as pjoin,
                     basename as pbasename,
                     dirname as pdirname,
                     isfile,
                     islink,
                     )
from shutil import copy
from collections import defaultdict
from glob import glob
import subprocess as sp
import os
import stat
import hashlib

from log import debug, warning
from settings import Settings
from exception import FileSyntaxError, BuildingError


class Cook(object):
    def __init__(self, package, env=None, qpkg_dir='./'):
        self._package = package
        self._env = env
        self._label = '[{}: {}_{}] '.format(env['QPKG_SOURCE'],
                                            env['QPKG_PACKAGE'],
                                            env['QPKG_ARCHITECTURE'])

    # https://www.debian.org/doc/manuals/maint-guide/dother.en.html#dirs
    def dirs(self):
        debug(self._label + 'create directories')
        src_install = pjoin(Settings.CONTROL_PATH,
                            self._package['package'] + '.dirs')
        if not pexists(src_install):
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    line = line.strip()
                    if line.startswith('/'):
                        raise FileSyntaxError(src_install, lineno, line)
                    dst = pjoin(self._env['QPKG_DEST_DATA'], line)
                    if not pexists(dst):
                        makedirs(dst)
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    # https://www.debian.org/doc/manuals/maint-guide/dother.en.html#install
    def install(self):
        debug(self._label + 'install files')
        src_install = pjoin(Settings.CONTROL_PATH,
                            self._package['package'] + '.install')
        if not pexists(src_install):
            warning('Missing: ' + src_install)
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    src, dst = line.strip().split(' ', 1)
                    dst = dst.strip()
                    if dst.startswith('/'):
                        dst = '.' + dst
                    dst = pjoin(self._env['QPKG_DEST_DATA'], dst)
                    if not pexists(dst):
                        makedirs(dst)
                    src_files = glob(src)
                    if not src_files:
                        raise FileSyntaxError(src_install,
                                              lineno,
                                              '`{}` not found'.format(src))
                    for fn in glob(src):
                        try:
                            sp.check_call(['cp', '-a', fn, dst])
                        except sp.CalledProcessError as e:
                            warning('Error in copy files: {}'.format(e))
                            return -1
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    # https://www.debian.org/doc/manuals/maint-guide/dother.en.html#links
    def links(self):
        debug(self._label + 'create additional symlinks')
        src_install = pjoin(Settings.CONTROL_PATH,
                            self._package['package'] + '.links')
        if not pexists(src_install):
            return
        try:
            lineno = 0
            with open(src_install) as fin:
                for line in fin:
                    lineno += 1
                    src, dst = line.strip().split(' ', 1)
                    dst = dst.strip()
                    if dst.startswith('/'):
                        dst = '.' + dst
                    dst = pjoin(self._env['QPKG_DEST_DATA'], dst)
                    if dst.endswith('/'):
                        if not pexists(dst):
                            makedirs(dst)
                        dst = pjoin(dst, pbasename(src))
                    else:
                        if not pexists(pdirname(dst)):
                            makedirs(pdirname(dst))
                    symlink(src, dst)
        except ValueError:
            raise FileSyntaxError(src_install, lineno, line)

    def controls(self):
        debug(self._label + 'control files')
        package = self._package
        suffix_normal = ['.conf', '.conffiles', '.mime', '.service']
        suffix_script = ['.init', '.preinst', '.postinst', '.prerm', '.postrm']
        dest_base = pjoin(self._env['QPKG_DEST_DATA'], '.qdk2')
        makedirs(dest_base)
        for suffix in suffix_normal + suffix_script:
            src = pjoin(Settings.CONTROL_PATH, package['package'] + suffix)
            dest = pjoin(dest_base, package['package'] + suffix)
            if not pexists(src):
                continue
            if suffix in ('.init',):
                dest = pjoin(self._env['QPKG_DEST_DATA'],
                             package['package'] + suffix)

            # copy to destination and replace template variables
            tpl_vars = [('%' + k + '%', v) for k, v in self._env.iteritems()
                        if k.startswith('QPKG_')]
            with open(src, 'r') as fin, open(dest, 'w+') as fout:
                for line in fin:
                    for k, v in tpl_vars:
                        line = line.replace(k, v)
                    fout.write(line)
            if suffix in suffix_script:
                chmod(dest, 0755)
            else:
                chmod(dest, 0644)

    def icons(self):
        debug(self._label + 'icon files')
        dest_base = pjoin(self._env['QPKG_DEST_CONTROL'], 'icons')
        makedirs(dest_base)
        package_name = self._package['package']
        icons = (('.icon.64', '.gif'), ('.icon.80', '_80.gif'),
                 ('.icon.gray', '_gray.gif'),
                 )
        for suffix, rsuffix in icons:
            src = pjoin(Settings.CONTROL_PATH, package_name + suffix)
            dest = pjoin(dest_base, package_name + rsuffix)
            if not pexists(src):
                warning('Missing: ' + src)
                copy(pjoin(Settings.TEMPLATE_PATH, Settings.CONTROL_PATH,
                           Settings.DEFAULT_PACKAGE + suffix), dest)
                continue
            copy(src, dest)
            chmod(dest, 0644)

    def package_routines(self):
        debug(self._label + 'package_routines')
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

    def qpkg_cfg(self):
        debug(self._label + 'qpkg_cfg')
        # check essential fields
        essential_fields = ('QPKG_PACKAGE', 'QPKG_VERSION', 'QPKG_MAINTAINER')
        for field in essential_fields:
            if field not in self._env or not self._env[field]:
                raise BuildingError('QPKG essential fields: {}'
                                    .format(', '.join(essential_fields)))
        # qpkg.cfg template
        content = [
            r'QPKG_NAME="{0[QPKG_PACKAGE]}"',
            r'QPKG_DISPLAYNAME="{0[QPKG_Q_APPNAME]}"',
            r'QPKG_VER="{0[QPKG_VERSION]}"',
            r'QPKG_AUTHOR="{0[QPKG_MAINTAINER]}"',
            r'QPKG_LICENSE="{0[QPKG_LICENSE]}"',
            r'QPKG_SUMMARY="{0[QPKG_DESCRIPTION]}"',
            r'QPKG_REQUIRE="{0[QPKG_DEPENDS]}"',
            r'QPKG_CONFLICT="{0[QPKG_CONFLICTS]}"',
            r'QPKG_CONFIG="{0[QPKG_CONFIG]}"',

            r'QPKG_RC_NUM="{0[QPKG_Q_RC_NUM]}"',
            r'QPKG_SERVICE_PROGRAM="{0[QPKG_INIT]}"',
            r'QPKG_SERVICE_PORT="{0[QPKG_Q_SERVICE_PORT]}"',
            r'QPKG_SERVICE_PIDFILE="{0[QPKG_Q_SERVICE_PIDFILE]}"',

            r'QPKG_WEBUI="{0[QPKG_Q_WEBUI]}"',
            r'QPKG_WEB_PORT="{0[QPKG_Q_WEB_PORT]}"',

            r'QPKG_ROOTFS="{0[QPKG_Q_ROOTFS]}"',
            r'QPKG_SERVICE_PROGRAM_CHROOT="{0[QPKG_Q_SERVICE_PROGRAM_CHROOT]}"'
        ]

        env = defaultdict(str)
        for k, v in self._env.iteritems():
            if k.startswith('QPKG_'):
                env[k] = v
        with open(pjoin(self._env['QPKG_DEST_CONTROL'],
                        'qpkg.cfg'), 'w+') as f:
            f.write(('\n'.join(content)).format(env))

    def list(self):
        debug(self._label + 'list')
        # list
        #   links
        #   dirs
        pass

    def conffiles(self):
        debug(self._label + 'conffiles')
        etc_path = pjoin(self._env['QPKG_DEST_DATA'], 'etc')
        conffiles = pjoin(self._env['QPKG_DEST_CONTROL'], 'conffiles')
        with open(conffiles, 'w+') as fout:
            conf_list = []
            for root, dirs, files in walk(etc_path):
                for f in files:
                    if isfile(pjoin(root, f)) and not islink(pjoin(root, f)):
                        conf_list.append(
                            pjoin(root[len(self._env['QPKG_DEST_DATA']):], f))
            fout.writelines('\n'.join(conf_list))
            filesize = fout.tell()
        if filesize == 0:
            unlink(conffiles)

    def fixperms(self):
        debug(self._label + 'fixperms')
        data_root = self._env['QPKG_DEST_DATA']
        bin_path = ['bin', 'sbin', 'usr/bin', 'usr/sbin',
                    'usr/local/bin', 'usr/local/sbin', 'etc/init.d']
        for root, dirs, files in walk(data_root):
            fixperm = False
            if root in [pjoin(data_root, d) for d in bin_path]:
                chmod(root, 0755)
                fixperm = True
            for f in files:
                if isfile(pjoin(root, f)):
                    # check setuid/setgid bits permissions
                    fstat = os.stat(pjoin(root, f))
                    if fstat.st_mode & stat.S_ISUID:
                        warning('{} has setuid attribute'
                                .format(pjoin(root[len(data_root):], f)))
                    if fstat.st_mode & stat.S_ISGID:
                        warning('{} has setgid attribute'
                                .format(pjoin(root[len(data_root):], f)))
                    if fixperm:
                        chmod(pjoin(root, f), fstat.st_mode | 755)

    def signature(self):
        debug(self._label + 'signature')
        # TODO: add gpg
        with open(pjoin(self._env['QPKG_DEST_CONTROL'], 'qpkg-version'),
                  'w') as f:
            f.write(Settings.QPKG_VERSION)
        pass

    def md5sums(self):
        debug(self._label + 'md5sum')
        data_root = self._env['QPKG_DEST_DATA']
        md5sums = pjoin(self._env['QPKG_DEST_CONTROL'], 'md5sums')
        md5_list = []
        for root, dirs, files in walk(data_root):
            if root.startswith(pjoin(data_root, 'etc')):
                continue
            for f in files:
                fpath = pjoin(root, f)
                if isfile(fpath) and not islink(fpath):
                    md5_list.append('{}  {}'.format(
                        hashlib.md5(open(fpath).read()).hexdigest(),
                        fpath[len(data_root) + 1:]))

        with open(md5sums, 'w+') as fout:
            fout.writelines('\n'.join(md5_list))
            filesize = fout.tell()
        if filesize == 0:
            unlink(md5sums)

    def __exec(self, cmd):
        try:
            debug('command: ' + ' '.join(cmd))
            sp.check_call(cmd, env=self._env)
        except sp.CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
