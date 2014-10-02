#!/usr/bin/env python

from sys import version_info


class SysCheck(object):
    def __init__(self):
        self._warning = []
        self._error = []

    def report(self):
        for item in self.get_check_list():
            func = getattr(self, item)
            func()
        return self._warning, self._error

    def get_check_list(self):
        return [
            '_do_python_vesion',
        ]

    def _do_python_vesion(self):
        if not version_info[:2] == (2, 7):
            self._error.append('python version 2.7 required')


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
