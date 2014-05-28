#!/usr/bin/env python


class BaseCommand(object):
    def __init__(self, args=None, extra_args=None):
        self._args = args
        self._extra_args = extra_args


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
