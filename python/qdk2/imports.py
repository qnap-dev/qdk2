#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     realpath as prealpath,
                     basename as pbasename,
                     isdir,
                     )
from os import listdir, makedirs
from shutil import copy
from glob import glob
from exception import ContainerUnsupported

from basecommand import BaseCommand
from settings import Settings
from importuri import ImportURI
from container import Container
from archive import Archive
from versioncontrol import VersionControl
from log import info, error


class CommandImport(BaseCommand):
    key = 'import'
    help = 'create a new QPKG from the various source'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help=cls.help)
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-p', '--project', metavar='NAME',
                            default=Settings.DEFAULT_PROJECT,
                            help='project name (default: %(default)s)')
        parser.add_argument('-d', '--directory', metavar='PATH',
                            default='./',
                            help='destination folder (default: %(default)s)')
        group = parser.add_argument_group('import source')
        mgroup = group.add_mutually_exclusive_group(required=True)
        mgroup.add_argument('-a', '--archive', metavar='PATH',
                            help='import from contents of archive')
        mgroup.add_argument('-r', '--repository', metavar='URI',
                            help='import from {} repository'
                            .format('/'.join(VersionControl.SUPPORT_TYPES)))
        mgroup.add_argument('-c', '--container',
                            nargs=2, metavar=('CTYPE', 'CID'),
                            help='import from Linux container ({})'
                                 .format('/'.join(Container.SUPPORT_TYPES)))
        mgroup.add_argument('-s', '--sample', metavar='NAME',
                            choices=cls.get_sample_list(),
                            help='import from built-in samples: {}'
                            .format(', '.join(cls.get_sample_list())))

    @classmethod
    def get_sample_list(self):
        samples = glob(pjoin(Settings.SAMPLES_PATH, '*.tar.gz'))
        samples = [pbasename(sample)[:-7] for sample in samples]
        return samples

    def _import_archive(self):
        # TODO: code refactoring
        import_from = ImportURI(self._args.archive, self.directory)
        import_from.run()

    def _import_repository(self):
        # TODO: code refactoring
        import_from = ImportURI(self._args.repository, self.directory)
        import_from.run()

    def _import_container(self):
        ctype, cid = self._args.container
        container = Container()

        info('Copy container (switch to root)')
        if ctype == 'lxc':
            container.import_lxc(cid, self.directory)
        elif ctype == 'docker':
            container.import_docker(cid, self.directory)
        else:
            raise ContainerUnsupported(str(self._args.container))

        # TODO: check container type and copy this type config file(s)
        info('Copy container config files')
        for fn in glob(pjoin(Settings.TEMPLATE_PATH, 'container', '*')):
            dst = pjoin(self.directory, pbasename(fn))
            copy(fn, dst)

    def _import_sample(self):
        sample_file = pjoin(Settings.SAMPLES_PATH,
                            self._args.sample + '.tar.gz')

        archive = Archive()
        archive.decompress(sample_file, self.directory, 'tarball', strip=1)

    def import_source(self):
        source_types = ('archive', 'repository', 'container', 'sample')

        for src_type in source_types:
            pass

        if self._args.archive is not None:
            info('Import archive: ' + self._args.archive)
            self._import_archive()
        if self._args.repository is not None:
            info('Import repository: ' + self._args.repository)
            self._import_repository()
        if self._args.container is not None:
            info('Import container: ' + ' - '.join(self._args.container))
            self._import_container()
        if self._args.sample is not None:
            info('Import sample: ' + self._args.sample)
            self._import_sample()

    def run(self):
        if not pexists(self.directory):
            makedirs(self.directory)
        else:
            if isdir(self.directory):
                if listdir(self.directory):
                    error('Directory is not empty: ' + self.directory)
                    return -1
            else:
                error('This is not directory: ' + self.directory)
                return -1

        self.import_source()
        return 0

    @property
    def directory(self):
        if not hasattr(self, '_directory'):
            self._directory = pjoin(prealpath(self._args.directory),
                                    self._args.project)
        return self._directory


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
