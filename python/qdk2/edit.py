#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (join as pjoin,
                     exists as pexists,
                     abspath as pabspath,
                     )
import os

from basecommand import BaseCommand
from log import error
from settings import Settings
from controlfiles import ControlFile
from editor import Editor


class CommandEdit(BaseCommand):
    key = 'edit'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='edit QPKG control files')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('filename', metavar='FILENAME', nargs='?')

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

    def _get_support_control_files(self):
        static_files = ['changelog', 'control', 'rules']
        file_exts = ['conf', 'dirs', 'init', 'install', 'links',
                     'postinst', 'postrm', 'preinst', 'prerm']
        packages = []
        control = ControlFile(self.qpkg_dir)
        for k in control.packages:
            if control.packages[k]['package'] not in packages:
                packages.append(control.packages[k]['package'])
        cfiles = [name + '.' + ext for name in packages for ext in file_exts]
        cfiles = static_files + cfiles
        return cfiles

    def run(self):
        if self.qpkg_dir is None:
            error('Cannot find QNAP/control anywhere!')
            error('Are you in the source code tree?')
            return -1

        if self._args.filename is None:
            self._args.filename = 'control'

        cfiles = self._get_support_control_files()

        if self._args.filename not in cfiles:
            error('Support control files: {}'.format(', '.join(cfiles)))
            return -1

        filename = pjoin(self.qpkg_dir, Settings.CONTROL_PATH,
                         self._args.filename)

        editor = Editor()
        if not pexists(filename):
            editor.set_template_file(
                pjoin(Settings.TEMPLATE_PATH, Settings.CONTROL_PATH,
                      '{}{}'.format(Settings.DEFAULT_PACKAGE,
                                    filename[filename.rfind('.'):])))
        editor.open(filename)
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
