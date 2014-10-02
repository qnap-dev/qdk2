#!/usr/bin/env python

from os.path import (exists as pexists,
                     isdir)
from shutil import copyfile
import subprocess as sp

from log import warning, error
from archive import Archive
from versioncontrol import VersionControl


class ImportURI(object):
    def __init__(self, uri, directory):
        self._uri = uri.strip()
        self._src = None
        self._dst = directory
        self._vcs = None
        self._archive = None

    def run(self):
        if not self.prepare_src():
            error('Invalid or unsupport URI')
            return -1

        if self._vcs is not None:
            VersionControl.checkout(self._src, self._dst, self._vcs)
        else:
            if isdir(self._src):
                self.copytree_overwrite(self._src, self._dst)
            else:
                archive = Archive()
                ftype = archive.file_type(self._src)
                if ftype is not None:
                    archive.decompress(self._src, self._dst, ftype)
                else:
                    copyfile(self._src, self._dst)

    def prepare_src(self):
        # remote URI: http(s)
        if self._uri.startswith('http://') or self._uri.startswith('https://'):
            self._vcs = VersionControl.probe(self._uri)
            if self._vcs is not None:
                self._src = self._uri
            else:
                self._src = self.download(self._uri)
        # remote URI: ftp
        elif self._uri.startswith('ftp://'):
            self._src = self.download(self._uri)
        # local URI
        elif self._uri.startswith('file://'):
            self._vcs = VersionControl.probe(self._uri)
            if self._vcs is not None:
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


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
