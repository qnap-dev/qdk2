#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     dirname as pdirname,
                     basename as pbasename,
                     realpath as prealpath,
                     isdir,
                     )
from os import listdir, makedirs
from shutil import copytree, copy, rmtree, move
from basecommand import BaseCommand
from glob import glob
import fileinput


from settings import Settings
from exception import BaseStringException, UserExit
from log import info, error


class CommandCreate(BaseCommand):
    key = 'create'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='create template')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('--fmt-qdk1', action='store_true', default=False,
                            help='QDK1 format')
        parser.add_argument('-p', metavar='package_name',
                            default=Settings.DEFAULT_TEMPLATE,
                            help='package_name (Default: {0})'.format(
                                Settings.DEFAULT_TEMPLATE))
        parser.add_argument('-d', metavar='directory', default='./',
                            help='destination folder (Default: $PWD)')
        parser.add_argument('-s', '--sample-files', action='store_true',
                            default=False, help='.c, .so and doc samples')

    def format_qdk1(self):
        info('The template are putting to ' + self.directory)
        if pexists(self.directory):
            yn = raw_input('{} folder exists! Confirm? [Y/n] '.format(
                           self.directory))
            if len(yn) and yn[0].lower() == 'n':
                raise UserExit()
        else:
            makedirs(self.directory)
        for fn in glob(pjoin(Settings.TEMPLATE_V1_PATH, '*')):
            dest = pjoin(self.directory, pbasename(fn))
            if isdir(fn):
                copytree(fn, dest)
            else:
                copy(fn, dest)

    def format_qdk2(self):
        info('Create CONTROL at {}'.format(self.directory))
        if pexists(pjoin(self.directory, Settings.CONTROL_PATH)):
            yn = raw_input('{} folder exists! Delete? [Y/n] '.format(
                           pjoin(self.directory, Settings.CONTROL_PATH)))
            if len(yn) and yn[0].lower() == 'n':
                raise UserExit()
            rmtree(pjoin(self.directory, Settings.CONTROL_PATH))
        if not pexists(self.directory):
            makedirs(self.directory)

        info('Copy default CONTROL files to {}'.format(
            pjoin(self.directory, Settings.CONTROL_PATH)))
        copytree(pjoin(Settings.TEMPLATE_PATH,
                       Settings.DEFAULT_TEMPLATE,
                       Settings.CONTROL_PATH),
                 pjoin(self.directory, Settings.CONTROL_PATH))

        if self.sample_files:
            info('Copy samples')
            default_template_path = pjoin(Settings.TEMPLATE_PATH,
                                          Settings.DEFAULT_TEMPLATE)
            for fn in listdir(default_template_path):
                fn = pjoin(default_template_path, fn)
                dest = pjoin(self.directory, pbasename(fn))
                if isdir(fn):
                    dest = pjoin(self.directory, pbasename(fn))
                    if not pexists(dest):
                        copytree(fn, dest)
                else:
                    copy(fn, dest)
        if self.package_name != Settings.DEFAULT_TEMPLATE:
            info('Modify package name to ' + self.package_name)
            # sed control, *.init, rules, *.conf
            files_check = ('control', 'rules', 'foobar.init', 'foobar.conf')
            for fn in files_check:
                fp = pjoin(self.directory, Settings.CONTROL_PATH, fn)
                for line in fileinput.input(fp, inplace=True):
                    print line.replace(Settings.DEFAULT_TEMPLATE,
                                       self.package_name),
                    # Python 3
                    # print(line.replace(DEFAULT_TEMPLATE, self.package_name),
                    #       end='')
            # mv foobar.* to self.package_name.*
            for fn in glob(pjoin(self.directory, Settings.CONTROL_PATH,
                                 Settings.DEFAULT_TEMPLATE + '.*')):
                move(fn, pjoin(pdirname(fn),
                               self.package_name + fn[fn.rindex('.'):]))

    def run(self):
        try:
            if self._args.fmt_qdk1:
                self.format_qdk1()
            else:
                self.format_qdk2()
        except BaseStringException as e:
            error(str(e))
            return -1
        return 0

    @property
    def package_name(self):
        return self._args.p

    @property
    def directory(self):
        if not hasattr(self, '_directory'):
            self._directory = prealpath(self._args.d)
        return self._directory

    @property
    def sample_files(self):
        return self._args.sample_files


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
