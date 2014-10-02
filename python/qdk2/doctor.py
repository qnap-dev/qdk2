#!/usr/bin/env python

from argparse import SUPPRESS

from basecommand import BaseCommand
from check import SysCheck
from log import warning, error


class CommandDoctor(BaseCommand):
    key = 'doctor'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key,
                                      help='check your system for problems')
        parser.add_argument('--' + cls.key, help=SUPPRESS)

    def run(self):
        sys_check = SysCheck()
        sys_warning, sys_error = sys_check.report()

        if not sys_warning and not sys_error:
            print 'Your system is ready for QDK2.'
            return 0

        if sys_warning:
            for msg in sys_warning:
                warning(msg)
        if sys_error:
            for msg in sys_error:
                error(msg)
        return -1


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
