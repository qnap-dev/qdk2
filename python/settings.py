#!/usr/bin/env python


import sys
from os import getenv
from os.path import (join as pjoin,
                     dirname as pdirname,
                     )

if sys.argv[0].startswith('/usr'):
    PREFIX = '/usr/share/qdk2'
    QDK_BINARY = 'QDK'
    QPKG_FILE = 'qpkg/qpkg_4.2.0_amd64.tgz'
else:
    PREFIX = pdirname(pdirname((sys.argv[0])))
    QDK_BINARY = 'QDK_2.2_amd64'
    QPKG_FILE = 'qpkg_4.2.0_amd64.tgz'


VERSION = 'v0.3-4-g05377f7'


class Settings(object):
    DEBUG = False if getenv('DEBUG') is None else True
    CONTROL_PATH = 'QNAP'
    DEFAULT_TEMPLATE = 'foobar'
    TEMPLATE_PATH = pjoin(PREFIX, 'template')
    TEMPLATE_V1_PATH = pjoin(PREFIX, QDK_BINARY, 'template')
    QBUILD = pjoin(PREFIX, QDK_BINARY, 'bin', 'qbuild')
    QPKG = pjoin(PREFIX, QPKG_FILE)


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
