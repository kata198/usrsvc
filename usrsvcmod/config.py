'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    'config' is the main config class used within usrsvc
'''

import os
import glob

from configobj import ConfigObj

from .MainConfig import MainConfig
from .ProgramConfig import ProgramConfig

__all__ = ('config', )

class config(object):

    def __init__(self, mainConfigFile):
        self.mainConfigFile = mainConfigFile

        self.isPared = False
        self.data = None

        self.mainConfig = None
        self.programConfigs = {}

    def parse(self):
        if not os.path.exists(self.mainConfigFile):
            raise ValueError('File does not exist: %s' %(self.mainConfigFile,))

        self.data = ConfigObj(self.mainConfigFile)
        
        self.mainConfig = MainConfig(**self.data['Main'])

        for key in self.data.keys():
            if key.startswith('Program:'):
                item = self.data[key]
                name = key[len('Program:'):]
                self.programConfigs[name] = ProgramConfig(name, **item)

        programConfigDir =  self.mainConfig.getProgramConfigDir()
        if programConfigDir:
            programConfigFiles = glob.glob(programConfigDir + '/*.cfg')
            for fname in programConfigFiles:
                data = ConfigObj(fname)
                for key in data.keys():
                    if key.startswith('Program:'):
                        item = data[key]
                        name = key[len('Program:'):]
                        self.programConfigs[name] = ProgramConfig(name, **item)



    def getProgramConfig(self, programName):
        return self.programConfigs[programName]

    def getProgramConfigs(self):
        return self.programConfigs
