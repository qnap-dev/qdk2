#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (join as pjoin,
                     exists as pexists,
                     abspath as pabspath,
                     )
#from shutil import rmtree
import os

from basecommand import BaseCommand
from log import error
#from controlfiles import ControlFile
from settings import Settings
from qbuild.rules import Rules


class CommandClean(BaseCommand):
    key = 'clean'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='clean QPKG')
        parser.add_argument('--' + cls.key, help=SUPPRESS)

    @property
    def qpkg_dir(self):
        if not hasattr(self, '_qpkg_dir'):
            cwd = os.getcwd()
            while cwd != '/':
                if pexists(pjoin(cwd, Settings.CONTROL_PATH, 'control')):
                    break
                cwd = pabspath(pjoin(cwd, os.pardir))
            self._qpkg_dir = cwd if cwd != '/' else None
        return self._qpkg_dir

    def run(self):
        if self.qpkg_dir is None:
            error('Cannot find QNAP/control anywhere!')
            error('Are you in the source code tree?')
            return -1

        rules = Rules()
        rules.clean()

        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
