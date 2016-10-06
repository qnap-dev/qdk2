#!/usr/bin/env python

from os.path import (exists as pexists,
                     join as pjoin,
                     realpath as prealpath,
                     )
from os import makedirs, chdir, getcwd, listdir
from shutil import rmtree, copytree
from controlfiles import ControlFile, ChangelogFile
from contextlib import contextmanager
import subprocess
import os

from settings import Settings
from log import info
from qbuild.rules import Rules
from qbuild.cook import Cook
from exception import BuildingError


class QbuildToQpkg(object):
    def __init__(self, path):
        self._path = path

    def build(self, args):
        cwd = getcwd()
        chdir(self._path)
        try:
            cmd = [Settings.QBUILD]
            if Settings.DEBUG:
                cmd.append('--verbose')
            else:
                cmd.append('-q')
            for extra in args._extra_args:
                cmd.append(extra)
            info(cmd)
            subprocess.check_call(cmd)
        finally:
            chdir(cwd)
        for fname in listdir(pjoin(self._path, 'build')):
            if fname.endswith('.qpkg'):
                return pjoin(self._path, 'build', fname)
        raise BuildingError('No *.qpkg found in ' + pjoin(self._path, 'build'))


class Qdk2ToQbuild(object):
    def __init__(self, data):
        self.build_dir = data.build_dir
        self.qpkg_dir = data.qpkg_dir

    def transform(self):
        cfile = ControlFile(self.qpkg_dir)
        result = []
        with self._setup_all(cfile):
            for k in cfile.packages:
                result.append(self._transform_one(cfile.packages[k]))
        return result

    def _transform_one(self, package):
        with self._setup(package):
            rules = Rules(self._env, self.qpkg_dir)
            rules.build()
            rules.binary()

            recipes = ('dirs',
                       'install',
                       'links',
                       'controls',
                       'icons',
                       'package_routines',
                       'qpkg_cfg',
                       'list',
                       'conffiles',
                       'fixperms',
                       'signature',
                       'md5sums',
                       )

            cook = Cook(package, self._env)
            for recipe in recipes:
                # TODO: handle cook status
                getattr(cook, recipe)()
            return self._env['QPKG_DEST_CONTROL']

    @contextmanager
    def _setup_all(self, control):
        cwd = getcwd()
        dest = prealpath(pjoin(self.build_dir, control.source['source']))
        if pexists(dest):
            rmtree(dest)
        if not pexists(self.build_dir):
            makedirs(self.build_dir)
        # if dest in qpkg_dir
        copytree(self.qpkg_dir, dest, True)
        self.source = control.source
        chdir(dest)

        yield None

        chdir(cwd)
        del self.source

    @contextmanager
    def _setup(self, package):
        def prepare_dest():
            dest = prealpath(pjoin(
                '.', Settings.CONTROL_PATH,
                package['package'] + '_' + package['architecture']))
            if pexists(dest):
                rmtree(dest)
            self._env['QPKG_DEST_CONTROL'] = dest
            self._env['QPKG_DEST_DATA'] = pjoin(dest, 'shared')
            makedirs(self._env['QPKG_DEST_DATA'])

        def prepare_env():
            myenv = os.environ.copy()
            for k, v in self.package.iteritems():
                myenv['QPKG_' + k.upper().replace('-', '_')] = v
            for k, v in self.source.iteritems():
                myenv['QPKG_' + k.upper().replace('-', '_')] = v
            myenv['QPKG_VERSION'] = ChangelogFile().version
            if pexists(pjoin(Settings.CONTROL_PATH,
                             package['package'] + '.init')):
                myenv['QPKG_INIT'] = package['package'] + '.init'
            self._env = myenv

        self.package = package
        prepare_env()
        prepare_dest()

        yield None

        del self._env
        del self.package


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
