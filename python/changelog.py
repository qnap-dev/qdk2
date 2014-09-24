#!/usr/bin/env python

from argparse import SUPPRESS
from os import getenv
from os.path import exists as pexists
from shutil import copy
import tempfile
import subprocess
import os

from basecommand import BaseCommand
from log import error, info
from controlfiles import ControlFile, ChangelogFile


class CommandChangelog(BaseCommand):
    key = 'changelog'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='modify QPKG changelog')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('--qpkg-dir',
                            default='./',
                            help='source package path (default: %(default)s)')
        parser.add_argument('-m', '--message', nargs="*",
                            default=None,
                            help='log message(s)')
        parser.add_argument('-v', '--version',
                            default=None,
                            help='this specifies the version number')
        parser.add_argument('-q', '--quiet', action="store_true",
                            default=False,
                            help='quiet mode')

    def append(self, fields):
        pass

    def parse(self, dest='./'):
        return ChangelogFile(dest)

    @property
    def qpkg_dir(self):
        if not hasattr(self, '_qpkg_dir'):
            self._qpkg_dir = self._args.qpkg_dir
        return self._qpkg_dir

    @property
    def author(self):
        if not hasattr(self, '_author'):
            self._author = getenv('QPKG_NAME')
            if self._author is None:
                self._author = ''
        return self._author

    @property
    def email(self):
        if not hasattr(self, '_email'):
            self._email = getenv('QPKG_EMAIL')
            if self._email is None:
                self._email = ''
        return self._email

    def run(self):
        control = ControlFile(self.qpkg_dir)
        changelog = ChangelogFile(self.qpkg_dir)
        kv = {'package_name': control.source['source']}
        if self._args.message is not None:
            kv['messages'] = self._args.message
        if self._args.version is not None:
            kv['version'] = self._args.version
        kv['author'] = self.author
        kv['email'] = self.email
        if len(kv['author']) == 0 or len(kv['email']) == 0:
            error('Environment variable QPKG_NAME or QPKG_EMAIL are empty')
            info('QPKG_NAME: ' + kv['author'])
            info('QPKG_EMAIL: ' + kv['email'])
            yn = raw_input('Continue? (Y/n) ')
            if yn.lower() == 'n':
                return 0
            kv['author'] = 'noname'
            kv['email'] = 'noname@local.host'
        entry = changelog.format(**kv)
        fid, filename = tempfile.mkstemp()
        os.close(fid)
        fd = open(filename, "w")
        fd.write(entry)
        if pexists(changelog.filename):
            with open(changelog.filename, 'r') as fread:
                fd.writelines(fread)
        fd.close()

        subprocess.check_call(['sensible-editor', filename])
        if not self._args.quiet and pexists(changelog.filename):
            yn = raw_input('Overwrite ' + changelog.filename + '? (Y/n) ')
            if yn.lower() == 'n':
                return 0
        copy(filename, changelog.filename)
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
