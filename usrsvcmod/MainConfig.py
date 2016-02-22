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

    def __init__(self, programConfigDir=None, pidfile=None):
        if programConfigDir and programConfigDir[-1] == '/':
            programConfigDir = programConfigDir[:-1]
        self.programConfigDir = programConfigDir
        self.pidfile = pidfile or (os.environ.get('HOME', '/tmp') + '/usrsvcd.pid')

    def getProgramConfigDir(self):
        return self.programConfigDir

    def __str__(self):
        return str(self.__dict__)
