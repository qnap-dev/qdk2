#!/usr/bin/env python

from os.path import (join as pjoin,
                     exists as pexists,
                     )
import subprocess as sp

from log import debug, warning
from settings import Settings
from exception import BuildingError


class Rules(object):
    SUPPORT_CMDS = ['build', 'binary', 'clean']

    def __init__(self, env=None, qpkg_dir='./'):
        self.env = env
        self.rules = pjoin(qpkg_dir, Settings.CONTROL_PATH, 'rules')
        if not pexists(self.rules):
            raise BuildingError('Missing: {}'
                                .format(pjoin(Settings.CONTROL_PATH, 'rules')))

    def __getattr__(self, name):
        if name in self.SUPPORT_CMDS:
            return lambda: self.__exec([self.rules, name])

        raise AttributeError("'{}' object has no attribute '{}'"
                             .format(self.__class__.__name__, name))

    def __exec(self, cmd):
        try:
            debug('command: ' + ' '.join(cmd))
            sp.check_call(cmd, env=self.env)
        except sp.CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
