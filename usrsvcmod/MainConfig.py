'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    'MainConfig' is the main configuration file
'''

import os

__all__ = ('MainConfig', )

class MainConfig(object):

    def __init__(self, config_dir=None, pidfile=None):
        if config_dir and config_dir[-1] == '/':
            config_dir = config_dir[:-1]
        self.config_dir = config_dir
        self.pidfile = pidfile or (os.environ.get('HOME', '/tmp') + '/usrsvcd.pid')

    def getProgramConfigDir(self):
        return self.config_dir

    def __str__(self):
        return str(self.__dict__)
