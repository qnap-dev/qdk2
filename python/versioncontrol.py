#!/usr/bin/env python

import subprocess as sp

from log import error


class VersionControl(object):
    SUPPORT_TYPES = ('git', 'svn', 'hg')
    GITHUB_REPO_PREFIX = 'https://github.com/'

    @classmethod
    def probe(self, url):
        probe_cmds = [
            ['git', 'ls-remote', url],
            ['svn', 'info', url],
            ['hg', 'identify', url],
        ]

        for cmd in probe_cmds:
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True)
            stdoutdata, stderrdata = p.communicate()
            if p.returncode == 0:
                return cmd[0]
        if self.is_github_repo(url):
            return 'github'
        return None

    @classmethod
    def is_github_repo(self, repository):
        if repository.count('/') == 1:
            cmd = ['git', 'ls-remote', self.GITHUB_REPO_PREFIX + repository]
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True)
            stdoutdata, stderrdata = p.communicate()
            if p.returncode == 0:
                return True
        return False

    @classmethod
    def checkout(self, url, path, vtype='git'):
        try:
            if vtype == 'git':
                sp.check_call(['git', 'clone', url, path])
            elif vtype == 'github':
                url = self.GITHUB_REPO_PREFIX + url
                sp.check_call(['git', 'clone', url, path])
            elif vtype == 'svn':
                sp.check_call(['svn', 'checkout', url, path])
            elif vtype == 'hg':
                sp.check_call(['hg', 'clone', url, path])
        except sp.CalledProcessError as e:
            error('Error in checkout VCS: {}'.format(e))
            return -1
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
