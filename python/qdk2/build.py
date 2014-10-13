#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (join as pjoin,
                     basename as pbasename,
                     abspath as pabspath,
                     exists as pexists,
                     )
from shutil import move
import os

from basecommand import BaseCommand
from settings import Settings
from qbuild import Qdk2ToQbuild, QbuildToQpkg
from log import info, error, debug
# from lint import CommandLint
from exception import BaseStringException


class CommandBuild(BaseCommand):
    key = 'build'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='build QPKG')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('--qpkg-dir', metavar='PATH',
                            default='./',
                            help='source package (default: %(default)s)')
        parser.add_argument('--build-dir', metavar='PATH',
                            default='../build-area',
                            help='folder to store building stuff'
                                 ' (default: %(default)s)')
        parser.add_argument('--as-qdk1', action='store_true',
                            default=False,
                            help='source package is QDK 1 format')

    @property
    def qpkg_dir(self):
        if not hasattr(self, '_qpkg_dir'):
            cwd = pabspath(self._args.qpkg_dir)
            while cwd != '/':
                if pexists(pjoin(cwd, Settings.CONTROL_PATH, 'control')):
                    break
                cwd = pabspath(pjoin(cwd, os.pardir))
            self._qpkg_dir = cwd if cwd != '/' else None

        return self._qpkg_dir

    @property
    def build_dir(self):
        if not hasattr(self, '_build_dir'):
            self._build_dir = self._args.build_dir
        return self._build_dir

    def run(self, **kargs):
        if self.qpkg_dir is None:
            error('Cannot find QNAP/control anywhere!')
            error('Are you in the source code tree?')
            return -1

        # Act as QDK1
        if self._args.as_qdk1:
            # TODO: build as qdk1 flow
            q = self._args.qpkg_dir
            result = QbuildToQpkg(q).build(self)
            arch = '_i386'
            dest = pjoin(self.build_dir,
                         pbasename(result)[:-5] + arch + '.qpkg')
            move(result, dest)
            info('Package is ready: ' + dest)
            return 0

        # Act as QDK2
        try:
            qbuild_formats = Qdk2ToQbuild(self).transform()
            for q in qbuild_formats:
                debug(q)
                result = QbuildToQpkg(q).build(self)
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
