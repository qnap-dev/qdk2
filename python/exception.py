#!/usr/bin/env python


class BaseStringException(Exception):
    def __init__(self, data=None):
        self._data = data if data is not None else ''
        self._msg = '{}: {}'.format(
            self.__class__.__name__,
            self._data)

    def __str__(self):
        return self._msg


class UserExit(BaseStringException):
    pass


class BuildingError(BaseStringException):
    pass


class ControlFileSyntaxError(BaseStringException):
    pass


class ChangelogFileSyntaxError(BaseStringException):
    def __init__(self, filename, line, msg=''):
        super(self.__class__, self).__init__()
        self._msg = 'ChangeFile Syntax Error ({}:{}): {}'.format(
            filename, line, msg)


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
