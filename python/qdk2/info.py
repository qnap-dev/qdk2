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
from controlfiles import ControlFile, ChangelogFile


class CommandInfo(BaseCommand):
    key = 'info'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='show QPKG information')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('--show-env', action='store_true',
                            default=False,
                            help='print environment')

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

    def print_source(self):
        print '[Source]'
        for k, v in sorted(self.cfile.source.iteritems()):
            print '  %-*s : %s' % (self._klen,
                                   'QPKG_' + k.upper(), v)
        print

    def print_package(self, package):
        print '  * {}'.format(package)
        for k, v in sorted(self.cfile.packages[package].iteritems()):
            print '  %-*s : %s' % (self._klen,
                                   'QPKG_' + k.upper(), v)
        print

    def print_all_packages(self):
        print '[Packages]'
        for k in sorted(self.cfile.packages.iterkeys()):
            self.print_package(k)

    def print_env(self):
        if not self._args.show_env:
            return
        print '[Environment]'
        for k, v in os.environ.iteritems():
            if k.startswith('LESS_TERMCAP_'):
                continue
            print '  %-*s : %s' % (self._klen, k, v)

    def _prepare(self):
        self._klen = 0
        for k in self.cfile.source.iterkeys():
            _klen = len('QPKG_') + len(k)
            self._klen = self._klen if self._klen > _klen else _klen

        for k in self.cfile.packages.iterkeys():
            self._klen = self._klen if self._klen > len(k) else len(k)

            initfile = self.cfile.packages[k]['package'] + '.init'
            if pexists(pjoin(self.qpkg_dir, Settings.CONTROL_PATH, initfile)):
                self.cfile.packages[k]['init'] = initfile

            config = self.cfile.packages[k]['package'] + '.conf'
            if pexists(pjoin(self.qpkg_dir, Settings.CONTROL_PATH, config)):
                self.cfile.packages[k]['config'] = config

        if self._args.show_env:
            for k in sorted(os.environ):
                self._klen = self._klen if self._klen > len(k) else len(k)

    def run(self):
        if self.qpkg_dir is None:
            error('Cannot find QNAP/control anywhere!')
            error('Are you in the source code tree?')
            return -1

        self.cfile = ControlFile(self.qpkg_dir)
        self.cfile.source['version'] = ChangelogFile().version

        self._prepare()

        self.print_source()
        self.print_all_packages()
        self.print_env()

        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
