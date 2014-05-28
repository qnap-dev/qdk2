#!/usr/bin/env python

from argparse import SUPPRESS
from basecommand import BaseCommand
from log import info


class CommandLint(BaseCommand):
    key = 'lint'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='build QPKG')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-d', metavar='directory',
                            help='destination folder')

    def lint(self, qpkg_dir):
        pass

    def run(self):
        info(str(self.__class__))
        # check package_name
        # control file format


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
