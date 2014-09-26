#!/usr/bin/env python

from os import makedirs
from os.path import (exists as pexists,
                     isdir)
from shutil import copyfile
import subprocess as sp

from log import warning


class ImportURI(object):
    TARBALL_EXTS = ['.tar', '.tar.gz', '.tar.bz2', '.tar.xz',
                    '.tgz', '.tb2', '.tbz2', '.txz']

    def __init__(self, uri, directory):
        self._uri = uri.strip()
        self._src = None
        self._dst = directory
        self._vcs = None
        self._archive = None

    def run(self):
        if not self.prepare_src():
            warning('Invalid or unsupport URI')
            return -1

        if self._vcs is not None:
            self.vcs_checkout(self._src, self._dst)
        else:
            if isdir(self._src):
                self.copytree_overwrite(self._src, self._dst)
            else:
                if self.archive_probe(self._src):
                    self.decompress(self._src, self._dst)
                else:
                    copyfile(self._src, self._dst)

    def prepare_src(self):
        # remote URI: http(s)
        if self._uri.startswith('http://') or self._uri.startswith('https://'):
            if self.vcs_probe(self._uri):
                self._src = self._uri
            else:
                self._src = self.download(self._uri)
        # remote URI: ftp
        elif self._uri.startswith('ftp://'):
            self._src = self.download(self._uri)
        # local URI
        elif self._uri.startswith('file://'):
            if self.vcs_probe(self._uri):
                self._src = self._uri
        # local file / dir
        else:
            self._src = self._uri if pexists(self._uri) else None

        return False if self._src is None else True

    def copytree_overwrite(self, src, dst):
        try:
            sp.check_call(['cp', '-a', src, dst])
        except sp.CalledProcessError as e:
            warning('Error in copying: {}'.format(e))

    def download(self, uri):
        # wget --trust-server-names http://ftp.gnu.org/gnu/wget/wget-1.15.tar.xz

        # TODO: return download file path / None
        return None

    def vcs_probe(self, uri):
        probe_cmds = [
            ['git', 'ls-remote', uri],
            ['svn', 'info', uri]
        ]

        for cmd in probe_cmds:
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True)
            stdoutdata, stderrdata = p.communicate()
            if p.returncode == 0:
                self._vcs = cmd[0]
                break
        return False if self._vcs is None else True

    def vcs_checkout(self, uri, path):
        try:
            if self._vcs == 'git':
                sp.check_call(['git', 'clone', uri, path])
            elif self._vcs == 'svn':
                sp.check_call(['svn', 'checkout', uri, path])
        except sp.CalledProcessError as e:
            warning('Error in checkout VCS: {}'.format(e))
            return -1
        return 0

    def archive_probe(self, filename):
        if filename.endswith('.zip'):
            self._archive = 'zip'
        elif filename.endswith('.7z'):
            self._archive = '7z'
        for ext in self.TARBALL_EXTS:
            if filename.endswith(ext):
                self._archive = 'tarball'
        return False if self._archive is None else True

    def decompress(self, filename, directory):
        if not pexists(directory):
            makedirs(directory)
        # TODO: tar strip-components feature
        try:
            # zip
            if self._archive == 'zip':
                sp.check_call(['unzip', '-o', filename, '-d', directory])
            # 7z
            elif self._archive == '7z':
                sp.check_call(['7z', '-y', 'x', filename, '-o' + directory])
            # tarball
            elif self._archive == 'tarball':
                sp.check_call(['tar', 'xvf', filename, '-C', directory])
        except sp.CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
