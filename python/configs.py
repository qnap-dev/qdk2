#!/usr/bin/env python

from os import getenv
from os.path import join as pjoin
import ConfigParser

from log import debug


class QDKrc(object):
    def __init__(self):
        self._sys_cfg = '/etc/qdkrc'
        self._usr_cfg = pjoin(getenv("HOME"), '.qdkrc')
        self._parsed = False
        self._config = {}
        self._field = {
            'user': {
                'name': {'type': 'str', 'default': ''},
                'email': {'default': ''}
            }
        }

    def parse(self):
        if self._parsed:
            return
        self._parsed = True
        config = ConfigParser.ConfigParser()
        candidates = [self._sys_cfg, self._usr_cfg]

        if not config.read(candidates):
            debug('qdkrc not found: ' + str(candidates))

        for s_name, s_value in self._field.items():
            self._config[s_name] = {}

            if not config.has_section(s_name):
                config.add_section(s_name)
            for o_name in s_value:
                if 'type' not in s_value[o_name]:
                    s_value[o_name]['type'] = 'str'
                o_type = s_value[o_name]['type']
                if config.has_option(s_name, o_name):
                    if o_type == 'str':
                        cfg_optget = config.get
                    elif o_type in ['int', 'float', 'boolean']:
                        cfg_optget = getattr(config, 'get' + o_type)
                    else:
                        raise Exception('Invalid option type: ' + o_type)
                    o_value = cfg_optget(s_name, o_name)
                else:
                    if 'default' in s_value[o_name]:
                        o_value = s_value[o_name]['default']
                    else:
                        o_value = None
                self._config[s_name][o_name] = o_value

    @property
    def config(self):
        self.parse()
        return self._config


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
