#!/usr/bin/env python

from argparse import SUPPRESS

from basecommand import BaseCommand
from settings import VERSION


class CommandVersion(BaseCommand):
    key = 'version'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='show the QDK2 version'
                                                    ' information')
        parser.add_argument('--' + cls.key, help=SUPPRESS)

    def run(self):
        print VERSION


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
