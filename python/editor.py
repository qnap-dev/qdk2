#!/usr/bin/env python

from os.path import (exists as pexists,
                     getmtime as pgetmtime,
                     )
from shutil import copy
import subprocess as sp
import tempfile
import os

from log import debug, info
from exception import CommandExecError


class Editor(object):

    def __init__(self):
        self._template = None
        self._content = None

    def set_template_file(self, filename):
        self._template = filename

    def insert_content(self, content):
        self._content = content

    def open(self, filename):
        tmpfile = self.__prepare_file(filename, 'edit')
        last_mtime = pgetmtime(tmpfile)

        cmd = ['sensible-editor', tmpfile]
        try:
            debug('command: ' + ' '.join(cmd))
            sp.check_call(cmd)
        except sp.CalledProcessError as e:
            raise CommandExecError(e)

        if last_mtime != pgetmtime(tmpfile):
            copy(tmpfile, filename)
        else:
            info('{} unmodified; exiting.'.format(filename))
        os.unlink(tmpfile)

    def __prepare_file(self, filename, action):
        if self._template is not None:
            filename = self._template

        fid, tmpfile = tempfile.mkstemp()
        os.close(fid)

        fd = open(tmpfile, "w")
        if self._content:
            fd.write(self._content)
        if pexists(filename):
            with open(filename, 'r') as fread:
                fd.writelines(fread)
        fd.close()
        return tmpfile


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
