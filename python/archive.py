#!/usr/bin/env python

from os import makedirs
from os.path import exists as pexists
import subprocess as sp

from log import debug, warning


class Archive(object):
    SUPPORT_FORMATS = {
        'tarball': ['.tar', '.tar.gz', '.tar.bz2', '.tar.Z', '.tar.lz',
                    '.tar.lzma', '.tar.xz',
                    '.tgz', '.tbz', '.tbz2', '.tb2', '.taz', '.tlz', '.txz'],
        'zip': ['.zip'],
        '7z': ['.7z', '.zipx']
    }

    def __init__(self):
        self._use_sudo = False

    def use_sudo(self, use=False):
        self._use_sudo = use

    def file_type(self, filename):
        for ftype, exts in self.SUPPORT_FORMATS.iteritems():
            for ext in exts:
                if filename.endswith(ext):
                    return ftype
        return None

    def decompress(self, filename, directory, ftype='tarball', strip=0):
        if not pexists(directory):
            makedirs(directory)

        if ftype == 'tarball':
            cmd = ['tar', 'xvf', filename, '-C', directory]
            if strip != 0:
                cmd.append('--strip-components=' + str(strip))
        elif ftype == 'zip':
            cmd = ['unzip', '-o', filename, '-d', directory]
        elif ftype == '7z':
            cmd = ['7z', '-y', 'x', filename, '-o' + directory]
        self.__exec(cmd)

    def __exec(self, cmd):
        if self._use_sudo:
            cmd.insert(0, 'sudo')
        try:
            debug('command: ' + ' '.join(cmd))
            sp.check_call(cmd)
        except sp.CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
