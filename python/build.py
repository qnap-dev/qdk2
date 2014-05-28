#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     dirname as pdirname,
                     basename as pbasename,
                     realpath as prealpath,
                     isdir,
                     )
from os import makedirs
from shutil import copy, rmtree
import hashlib

from basecommand import BaseCommand
from log import info, trace
from lint import CommandLint
from controlfiles import ControlFile, ChangelogFile
from settings import Settings


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
                            default='./build-area',
                            help='Folder to store building stuff')
        parser.add_argument('--to-qbuild', action='store_true',
                            default=False,
                            help='translate QDK2 format to qbuild format')

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

    @trace
    def phase_qdk2_to_qbuild(self):
        pass

    @trace
    def phase_qbuild_to_qpkg(self):
        pass

    @trace
    def run(self, **kargs):
        for k in kargs:
            setattr(self, '_' + k, kargs[k])

        controlfile = ControlFile()
        for k in controlfile.packages:
            package = controlfile.packages[k]
            name = package['package']
            dest = pjoin(self.build_dir, name)
            if pexists(dest):
                rmtree(dest)
            makedirs(dest)
            ######## controls
            suffix_to_copy = ['.conffiles', '.postrm', '.prerm', '.postinst',
                              '.preinst', '.dirs', '.links', '.mime']
            for suffix in suffix_to_copy:
                src = pjoin(self.qpkg_dir, Settings.CONTROL_PATH,
                            name + suffix)
                if not pexists(src):
                    continue
                copy(src, dest)
            # package_routines
            # qpkg.cfg
            # shared/init.sh
            # conffiles
            # list
            #   links
            #   dirs
            # md5sum
            #   hashlib.md5(open("/tmp/lp-fish-tools_1.22.1.tar.gz").read()).hexdigest()
            ####### data
        ## phase_qdk2_to_qbuild
        #if isdir(self.build_dir):
        #    error = False
        #    # lint
        #    try:
        #        CommandLint().lint(self.qpkg_dir)
        #    except BaseStringException:
        #        error = True
        #    # TODO
        #    if error:
        #        pass
        #    self.phase_qdk2_to_qbuild()

        ## phase 2
        #self.phase_qbuild_to_qpkg()
        ## raise BuildingError(self.build_dir + ' not found')
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
