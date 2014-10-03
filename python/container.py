#!/usr/bin/env python

from os.path import join as pjoin
import subprocess as sp

from log import debug, warning


class Container(object):
    SUPPORT_TYPES = ('lxc', 'docker')

    def __init__(self):
        self._use_sudo = True

    def import_lxc(self, name, directory):
        # TODO: lxc-clone use rsync and it too slow
        cmds = [
            ['lxc-clone', '-P', directory, name, 'image'],
            ['tar', 'cf', pjoin(directory, 'image.tar'),
                '-C', directory, 'image'],
            ['rm', '-rf', pjoin(directory, 'image')]
        ]
        for cmd in cmds:
            self.__exec(cmd)

    def import_docker(self, img_id, directory):
        cmds = [
            ['docker', 'save', '-o', pjoin(directory, 'image.tar'), img_id]
        ]
        for cmd in cmds:
            self.__exec(cmd)

    def __exec(self, cmd):
        if self._use_sudo:
            cmd.insert(0, 'sudo')
        try:
            debug('command: ' + ' '.join(cmd))
            sp.check_call(cmd)
        except sp.CalledProcessError as e:
            warning('Error in extracting: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
