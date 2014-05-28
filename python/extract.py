#!/usr/bin/env python

from argparse import SUPPRESS
from basecommand import BaseCommand


from log import info


class CommandExtract(BaseCommand):
    key = 'extract'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='build QPKG')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-d', metavar='directory',
                            help='destination folder')

    @property
    def package_file(self):
        pass

    def run(self):
        info(str(self.__class__))


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
