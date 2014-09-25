#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     dirname as pdirname,
                     basename as pbasename,
                     realpath as prealpath,
                     isdir,
                     )
from os import listdir, makedirs, remove, getpid
from shutil import copytree, copy, rmtree, move
from basecommand import BaseCommand
from glob import glob
import fileinput
import subprocess as sp


from settings import Settings
from importuri import ImportURI
from exception import (BaseStringException,
                       UserExit,
                       ContainerUnsupported,
                       )
from log import info, error


class CommandCreate(BaseCommand):
    key = 'create'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='create QPKG template')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-p', '--package', metavar='name',
                            default=Settings.DEFAULT_PACKAGE,
                            help='package name (default: %(default)s)')
        parser.add_argument('-d', '--directory', metavar='path',
                            default='./',
                            help='destination folder (default: %(default)s)')
        parser.add_argument('-i', '--import-from', metavar='uri',
                            default=None,
                            help='import source code from URI')
        parser.add_argument('-t', '--template', metavar='type',
                            choices=Settings.SUPPORT_TEMPLATES,
                            default=None,
                            help='create new QPKG from existed template')
        parser.add_argument('-c', '--container',
                            nargs=2, metavar=('ctype', 'cid'),
                            help='e.g., -c lxc ubuntu | -c docker 826544226fdc')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--format-qdk1', action='store_true',
                           default=False,
                           help='QDK1 format (legacy)')
        group.add_argument('--format-qdk2', action='store_true',
                           default=True,
                           help='QDK2 format (default)')

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

        # copy template control files
        info('Copy default CONTROL files to {}'.format(
            pjoin(self.directory, Settings.CONTROL_PATH)))
        copytree(pjoin(Settings.TEMPLATE_PATH,
                       Settings.CONTROL_PATH),
                 pjoin(self.directory, Settings.CONTROL_PATH))

        # cook QNAP
        if self.template != '':
            for fn in glob(pjoin(self.directory, Settings.CONTROL_PATH,
                                 '*.sample')):
                dst = fn[:fn.rfind('.')]
                copy(fn, dst)
        samples = pjoin(self.directory, Settings.CONTROL_PATH, '*.sample')
        for fn in glob(samples):
            remove(fn)

        self.rename_ctrl_files()

    def import_from(self):
        if self._args.import_from is None:
            return

        import_uri = ImportURI(self._args.import_from, self.directory)
        import_uri.run()

    def copy_sample(self):
        # copy template data files
        if self.template in Settings.SUPPORT_TEMPLATES:
            info('Copy template data files: ' + self.template)
            default_template_path = pjoin(Settings.TEMPLATE_PATH,
                                          self.template)
            for fn in listdir(default_template_path):
                fn = pjoin(default_template_path, fn)
                dest = pjoin(self.directory, pbasename(fn))
                if isdir(fn):
                    if not pexists(dest):
                        copytree(fn, dest)
                else:
                    copy(fn, dest)

    def rename_ctrl_files(self):
        # rename
        if self.package_name != Settings.DEFAULT_CONTROL_PACKAGE:
            info('Modify package name to ' + self.package_name)
            # sed control, *.init, rules, *.conf
            files_check = ('control', 'rules', 'foobar.init', 'foobar.conf')
            for fn in files_check:
                fp = pjoin(self.directory, Settings.CONTROL_PATH, fn)
                for line in fileinput.input(fp, inplace=True):
                    print line.replace(Settings.DEFAULT_CONTROL_PACKAGE,
                                       self.package_name),

            # mv foobar.* to self.package_name.*
            for fn in glob(pjoin(self.directory, Settings.CONTROL_PATH,
                                 Settings.DEFAULT_CONTROL_PACKAGE + '.*')):
                move(fn, pjoin(pdirname(fn),
                               self.package_name + fn[fn.rindex('.'):]))

    def container(self):
        if self._args.container is None:
            return

        # TODO: check container type and copy this type config file(s)
        info('Copy container config files')
        for fn in glob(pjoin(Settings.TEMPLATE_PATH, 'container', '*')):
            dst = pjoin(self.directory, pbasename(fn))
            copy(fn, dst)

        info('Copy container (switch to root)')
        if self._args.container[0] == 'lxc':
            image_path = './'
            image_dir = 'image' + '-' + str(getpid())
            # TODO: lxc-clone use rsync and it too slow
            sp.call(['sudo', 'lxc-clone', '-P', image_path,
                     self._args.container[1], image_dir])
            info('compress')
            sp.call(['sudo', 'tar', 'cf', pjoin(self.directory, 'image.tar'),
                     image_path + image_dir])
            sp.call(['sudo', 'rm', '-rf', image_path + image_dir])
        elif self._args.container[0] == 'docker':
            sp.call(['sudo', 'docker', 'save', '-o',
                     pjoin(self.directory, 'image.tar'),
                     self._args.container[1],
                     ])
        else:
            raise ContainerUnsupported(str(self._args.container))

    def run(self):
        try:
            if self._args.format_qdk1:
                info('Build QPKG with QDK1 format')
                self.format_qdk1()
            if self._args.format_qdk2:
                info('Build QPKG with QDK2 format')
                self.format_qdk2()

            self.copy_sample()
            self.import_from()
            self.container()
        except UserExit:
            pass
        except BaseStringException as e:
            error(str(e))
            return -1
        return 0

    @property
    def package_name(self):
        return self._args.package

    @property
    def directory(self):
        if not hasattr(self, '_directory'):
            self._directory = pjoin(prealpath(self._args.directory),
                                    self.package_name)
        return self._directory

    @property
    def template(self):
        if not hasattr(self, '_template'):
            self._template = '' if self._args.template is None else self._args.template
        return self._template


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
