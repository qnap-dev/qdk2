#!/usr/bin/env python

import subprocess as sp

from log import warning


class VersionControl(object):
    @classmethod
    def probe(self, uri):
        probe_cmds = [
            ['git', 'ls-remote', uri],
            ['svn', 'info', uri]
        ]

        for cmd in probe_cmds:
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True)
            stdoutdata, stderrdata = p.communicate()
            if p.returncode == 0:
                return cmd[0]
        return None

    @classmethod
    def checkout(self, uri, path, vtype='git'):
        try:
            if vtype == 'git':
                sp.check_call(['git', 'clone', uri, path])
            elif vtype == 'svn':
                sp.check_call(['svn', 'checkout', uri, path])
        except sp.CalledProcessError as e:
            warning('Error in checkout VCS: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
