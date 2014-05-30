#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     isdir as pisdir
                     )
from os import makedirs
from shutil import copy, rmtree, copytree
import hashlib
import subprocess

from basecommand import BaseCommand
from log import info, trace
from lint import CommandLint
from controlfiles import ControlFile, ChangelogFile
from settings import Settings


class Qdk2ToQbuild(object):
    def __init__(self, data):
        self.build_dir = data.build_dir
        self.qpkg_dir = data.qpkg_dir

    def transform(self):
        controlfile = ControlFile()
        for k in controlfile.packages:
            self._transform_one(controlfile.packages[k])

    def _transform_one(self, package):
        self.package = package
        self._setup()
        self._build()
        self._binary()
        self._move_controls()
        self._cook_package_routines()
        self._cook_qpkg_cfg()
        self._cook_init_sh()
        self._cook_conffiles()
        self._cook_list()
        self._cook_md5sum()

    @trace
    def _setup(self):
        name = self.package['package']
        self._dest = pjoin(self.build_dir, name)
        if pexists(self._dest) and pisdir(self._dest):
            rmtree(self._dest)
        if not pexists(self.build_dir):
            makedirs(self.build_dir)
        # if dest in qpkg_dir
        copytree(self.qpkg_dir, self._dest)

    @trace
    def _build(self):
        subprocess.check_call([pjoin(self._dest,
                                     Settings.CONTROL_PATH,
                                     'rules'),
                               'build',
                               ])

    @trace
    def _binary(self):
        subprocess.check_call([pjoin(self._dest,
                                     Settings.CONTROL_PATH,
                                     'rules'),
                               'binary',
                               ])
        #if pexists(

    @trace
    def _move_controls(self):
        package = self.package
        suffix_to_copy = ['.conffiles', '.postrm', '.prerm', '.postinst',
                          '.preinst', '.dirs', '.links', '.mime']
        for suffix in suffix_to_copy:
            src = pjoin(self.qpkg_dir, Settings.CONTROL_PATH,
                        package['package'] + suffix)
            if not pexists(src):
                continue
            copy(src, self._dest)

    @trace
    def _cook_package_routines(self):
        # package_routines
        pass

    @trace
    def _cook_qpkg_cfg(self):
        # qpkg.cfg
        pass

    @trace
    def _cook_init_sh(self):
        # shared/init.sh
        pass

    @trace
    def _cook_conffiles(self):
        # conffiles
        pass

    @trace
    def _cook_list(self):
        # list
        #   links
        #   dirs
        pass

    @trace
    def _cook_md5sum(self):
        # md5sum
        #   hashlib.md5(open("/tmp/lp-fish-tools_1.22.1.tar.gz").read()).hexdigest()
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

    def phase_qbuild_to_qpkg(self):
        pass

    def run(self, **kargs):
        for k in kargs:
            setattr(self, '_' + k, kargs[k])

        Qdk2ToQbuild(self).transform()
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
