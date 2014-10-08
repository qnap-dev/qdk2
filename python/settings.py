#!/usr/bin/env python


import sys
from os import getenv
from os.path import (join as pjoin,
                     dirname as pdirname,
                     abspath as pabspath,
                     )

if sys.argv[0].startswith('/usr'):
    PREFIX = '/usr/share/qdk2'
    QDK_BINARY = 'QDK'
else:
    PREFIX = pdirname(pdirname(pabspath(sys.argv[0])))
    QDK_BINARY = 'QDK_2.2_amd64'


VERSION = 'v0.9-5-g67ff5b3'


class Settings(object):
    DEBUG = False if getenv('DEBUG') is None else True
    QPKG_VERSION = '2.2'
    CONTROL_PATH = 'QNAP'
    SUPPORT_TEMPLATES = ('c_cpp', 'custom-webserver', 'php', 'python', 'webapp')
    DEFAULT_PROJECT = 'new_project'
    DEFAULT_PACKAGE = 'foobar'
    SAMPLES_PATH = pjoin(PREFIX, 'samples')
    TEMPLATE_PATH = pjoin(PREFIX, 'template')
    TEMPLATE_V1_PATH = pjoin(PREFIX, QDK_BINARY, 'template')
    QBUILD = pjoin(PREFIX, QDK_BINARY, 'bin', 'qbuild')


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
