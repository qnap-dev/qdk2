#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     isdir as pisdir,
                     join as pjoin,
                     basename as pbasename,
                     )
from os import makedirs
from tempfile import mkdtemp
from shutil import rmtree, copy
from contextlib import contextmanager
from glob import glob
from subprocess import check_call
from subprocess import CalledProcessError

from log import error, debug, info, warning
from basecommand import BaseCommand
from settings import Settings


@contextmanager
def create_temp_direcory():
    tempd = mkdtemp()
    debug(tempd)

    yield tempd

    if not Settings.DEBUG:
        rmtree(tempd)


class CommandExtract(BaseCommand):
    key = 'extract'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='extract QNAP App (.qpkg)'
                                                    ' or firmware image (.img)')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        group = parser.add_argument_group('extract file type')
        mgroup = group.add_mutually_exclusive_group()
        mgroup.add_argument('--as-qpkg', action='store_true',
                            default=False,
                            help='treat as qpkg, ignore suffix')
        mgroup.add_argument('--as-image', action='store_true',
                            default=False,
                            help='treat as image, ignore suffix')
        parser.add_argument('-d', '--directory', metavar='PATH',
                            default='./',
                            help='extract file to specific directory'
                                 ' (default: %(default)s)')
        parser.add_argument('file', metavar='file',
                            help='such as TS-870_20140502-4.1.0.img'
                                 ' or photostation.qpkg')

    # FIXME: couldn't extract every qpkg and would return error(tar extract)
    def extract_qpkg(self, package, to):
        extractor = Settings.QBUILD
        check_call([extractor, '--extract', package, to])
        if not pexists(pjoin(to, 'shared')):
            makedirs(pjoin(to, 'shared'))
        data = glob(pjoin(to, 'data.*'))[0]
        try:
            check_call(['tar', 'xvf', data, '-C', pjoin(to, 'shared')])
        except CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))

    def extract_image(self, image, to):
        with create_temp_direcory() as d:
            check_call(['tar', 'xf', Settings.QPKG, '-C', d])
            tools_base = glob(pjoin(d, 'qpkg_*'))[0]
            extractor = pjoin(tools_base, 'PC1')
            info('Copy image to working area... ' + d)
            copy(image, pjoin(tools_base, 'cde-root'))
            info('Decrypting...')
            check_call([extractor, 'd', 'QNAPNASVERSION4', pbasename(image),
                        '/a.tgz'])
            info('Extracting...')
            check_call(['tar', 'xvf', pjoin(tools_base, 'cde-root', 'a.tgz'),
                        '-C', to])

    def run(self):
        directory = pjoin(self._args.directory)

        if pexists(directory) and not pisdir(directory):
            error('{} is not directory'.format(directory))
            return -1
        if not pexists(self._args.file) and pisdir(self._args.file):
            error('{} is not file'.format(self._args.file))
            return -1
        if not pexists(directory):
            makedirs(directory)
        if self._args.as_qpkg:
            self.extract_qpkg(self._args.file, directory)
        elif self._args.as_image:
            self.extract_image(self._args.file, directory)
        elif self._args.file.endswith('.img'):
            self.extract_image(self._args.file, directory)
        elif self._args.file.endswith('.qpkg'):
            self.extract_qpkg(self._args.file, directory)
        else:
            error('Unknown file suffix. Speicify --qpkg or --image')
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
