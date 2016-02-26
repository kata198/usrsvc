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

    def __init__(self, config_dir=None, pidfile=None, usrsvcd_stdout=None, usrsvcd_stderr=None, **kwargs):
        if kwargs:
            raise ValueError('Unknown config options in Main section: %s\n' %(str(kwargs.keys()),))

        if config_dir:
            if config_dir[0] != '/':
                raise ValueError('config_dir in [Main], if defined, must be an absolute path.')
            if config_dir[-1] == '/':
                config_dir = config_dir[:-1]

        self.config_dir = config_dir
        self.pidfile = pidfile or (os.environ.get('HOME', '/tmp') + '/usrsvcd.pid')
        if usrsvcd_stdout:
            if usrsvcd_stdout[0] != '/':
                raise ValueError('usrsvcd_stdout in [Main], if defined, must be an absolute path.')

        self.usrsvcd_stdout = usrsvcd_stdout

        if usrsvcd_stderr:
            if usrsvcd_stderr != 'stdout':
                if usrsvcd_stderr[0] != '/':
                    raise ValueError('usrsvcd_stderr in [Main], if defined, must be "stdout" or an absolute path.')

        self.usrsvcd_stderr = usrsvcd_stderr

    def getProgramConfigDir(self):
        return self.config_dir

    def __str__(self):
        return str(self.__dict__)
