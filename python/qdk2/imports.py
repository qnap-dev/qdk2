#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     realpath as prealpath,
                     basename as pbasename,
                     dirname as pdirname,
                     isdir,
                     )
from os import listdir, makedirs, chmod
from shutil import copytree, rmtree, move
from glob import glob
import subprocess as sp
import tempfile
import fileinput

from basecommand import BaseCommand
from settings import Settings
from container import Container
from archive import Archive
from versioncontrol import VersionControl
from log import info, error
from exception import ContainerUnsupported


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
        mgroup.add_argument('-a', '--archive', metavar='FILE',
                            help='archive file')
        mgroup.add_argument('-f', '--folder', metavar='PATH',
                            help='existing folder')
        mgroup.add_argument('-r', '--repository', metavar='URL',
                            help='{} repository'
                            .format('/'.join(VersionControl.SUPPORT_TYPES)))
        mgroup.add_argument('-c', '--container',
                            nargs=2, metavar=('CTYPE', 'CID'),
                            help='linux container ({})'
                                 .format('/'.join(Container.SUPPORT_TYPES)))
        mgroup.add_argument('-s', '--sample', metavar='NAME',
                            choices=cls.get_sample_list(),
                            help='built-in samples: {}'
                            .format(', '.join(cls.get_sample_list())))

    @classmethod
    def get_sample_list(self):
        samples = glob(pjoin(Settings.SAMPLES_PATH, '*.tar.gz'))
        samples = [pbasename(sample)[:-7] for sample in samples]
        return samples

    def _download(self, url):
        try:
            tmp_dir = tempfile.mkdtemp()
            cmd = ['wget', '--trust-server-names', url, '-P', tmp_dir]
            sp.check_call(cmd)
        except:
            error('Download error: ' + url)
            rmtree(tmp_dir, True)
            return None
        return glob(pjoin(tmp_dir, '*'))[0]

    def _import_archive(self, filename, directory):
        if filename.startswith('http://') \
                or filename.startswith('https://') \
                or filename.startswith('ftp://'):
            download_file = self._download(filename)
            filename = download_file

        if filename is None:
            return -1

        try:
            archive = Archive()
            ftype = archive.file_type(filename)
            if ftype is None:
                error('Invalid archive format: ' + filename)
                return -1
            archive.decompress(filename, directory, ftype)
        finally:
            if download_file is not None:
                rmtree(pdirname(download_file))
        return 0

    def _import_folder(self, path, directory):
        if not isdir(path):
            error('Invalid folder path: ' + path)
            return -1
        rmtree(directory)
        copytree(path, directory, True)
        return 0

    def _import_repository(self, url, directory):
        vcs = VersionControl.probe(url)
        if vcs is None:
            error('Unknown repository type: ' + url)
            return -1
        return VersionControl.checkout(url, directory, vcs)

    def _import_container(self, container, directory):
        ctype, cid = self._args.container
        container = Container()

        info('Copy container (switch to root)')
        if ctype == 'lxc':
            container.import_lxc(cid, self.directory)
        elif ctype == 'docker':
            container.import_docker(cid, self.directory)
        else:
            raise ContainerUnsupported(str(self._args.container))

        # cook container.json
        tpl_vars = [('@@IMAGE_ID@@', cid),
                    ('@@NAME@@', self._args.project),
                    ('@@TYPE@@', ctype)]
        src = pjoin(Settings.TEMPLATE_PATH, 'container', 'container.json')
        dst = pjoin(self.directory, 'container.json')
        with open(src, 'r') as fin, open(dst, 'w') as fout:
            for line in fin:
                for k, v in tpl_vars:
                    line = line.replace(k, v)
                fout.write(line)
        # cook QNAP control files
        makedirs(pjoin(self._directory, Settings.CONTROL_PATH))
        tpl_files = glob(pjoin(Settings.TEMPLATE_PATH, 'container',
                               Settings.CONTROL_PATH, '*'))
        for tpl in tpl_files:
            fn = pbasename(tpl)
            if fn.find('.') == -1:
                dst = pjoin(self._directory, Settings.CONTROL_PATH, fn)
            else:
                dst = pjoin(self._directory, Settings.CONTROL_PATH,
                            self._args.project + fn[fn.index('.'):])
            with open(tpl, 'r') as fin, open(dst, 'w') as fout:
                for line in fin:
                    line = line.replace('@@PACKAGE@@', self._args.project)
                    fout.write(line)
                if pbasename(dst) != 'control':
                    chmod(dst, 0755)
        return 0

    def _import_sample(self, name, directory):
        sample_file = pjoin(Settings.SAMPLES_PATH,
                            self._args.sample + '.tar.gz')

        archive = Archive()
        archive.decompress(sample_file, self.directory, 'tarball', strip=1)
        return 0

    def import_source(self, src_type, src_value):
        info('Import {}: {}'.format(src_type, str(src_value)))
        import_func = getattr(self, '_import_' + src_type)
        return import_func(src_value, self.directory)

    def probe_source_type(self):
        source_types = ('archive',
                        'folder',
                        'repository',
                        'container',
                        'sample')

        for src_type in source_types:
            src_value = getattr(self._args, src_type)
            if src_value is not None:
                return src_type, str(src_value)

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

        try:
            src_type, src_value = self.probe_source_type()
            if self.import_source(src_type, src_value) != 0:
                error('Import failed')

            if pexists(pjoin(self._directory, Settings.CONTROL_PATH)):
                info('{} folder exists!'.format(Settings.CONTROL_PATH))
                return 0

            # copy template control files
            info('Copy default CONTROL files to {}'.format(
                pjoin(self.directory, Settings.CONTROL_PATH)))
            copytree(pjoin(Settings.TEMPLATE_PATH, Settings.CONTROL_PATH),
                     pjoin(self.directory, Settings.CONTROL_PATH), True)

            info('Modify package name to ' + self._args.project)
            # sed control, rules, *.init, *.conf
            files_check = ('control', 'rules', 'foobar.init', 'foobar.conf')
            for fn in files_check:
                fp = pjoin(self.directory, Settings.CONTROL_PATH, fn)
                for line in fileinput.input(fp, inplace=True):
                    print line.replace(Settings.DEFAULT_PACKAGE,
                                       self._args.project),

            # mv foobar.* to self._args.project.*
            for fn in glob(pjoin(self.directory, Settings.CONTROL_PATH,
                                 Settings.DEFAULT_PACKAGE + '.*')):
                dest = pjoin(pdirname(fn),
                             self._args.project + fn[fn.index('.'):])
                move(fn, dest)
        except Exception as e:
            error(e)
            return -1
        return 0

    @property
    def directory(self):
        if not hasattr(self, '_directory'):
            self._directory = pjoin(prealpath(self._args.directory),
                                    self._args.project)
        return self._directory

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
