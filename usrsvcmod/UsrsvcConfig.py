'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv3.
    This may change at my discretion, retroactively, and without notice.

    You should have received a copy of this with the source distribution as a file titled, LICENSE.

    The most current license can be found at:
    https://github.com/kata198/usrsvc/LICENSE

    This location may need to be changed at some point in the future, in which case
    you are may email Tim Savannah <kata198 at gmail dot com>, or find them on the
    current website intended for distribution of usrsvc.



    'UsrsvcConfig' is the main config class used within usrsvc
'''

import copy
import os
import glob

from configobj import ConfigObj

from .MainConfig import MainConfig
from .ProgramConfig import ProgramConfig

__all__ = ('UsrsvcConfig', )

class UsrsvcConfig(object):
    '''
        UsrsvcConfig - The main config class. All other configs are accessable through this.
    '''

    def __init__(self, mainConfigFile):
        self.mainConfigFile = mainConfigFile

        self.isPared = False
        self.datas = None

        self.mainConfig = None
        self.programConfigs = {}

    def parse(self):
        '''
            parse - Parse the config data.
        '''
        if not os.path.exists(self.mainConfigFile):
            raise ValueError('File does not exist: %s' %(self.mainConfigFile,))

        self.datas = []
        self.filenames = [self.mainConfigFile]

        # Process main config
        mainData = ConfigObj(self.mainConfigFile)
        self.datas.append(mainData)

        if 'Main' not in mainData:
            raise ValueError('Missing [Main] section in main config. Required.')
        
        self.mainConfig = MainConfig(**mainData['Main'])

        self.defaultSettings = {}

        # Get additional configs, read all data.
        programConfigDir =  self.mainConfig.getProgramConfigDir()
        if programConfigDir:
            programConfigFiles = glob.glob(programConfigDir + '/*.cfg')
            for fname in programConfigFiles:
                data = ConfigObj(fname)
                self.datas.append(data)
                self.filenames.append(fname)

        # Run through all configs to gather DefaultSettings
        for i in range(len(self.datas)):
            data = self.datas[i]
            fname = self.filenames[i]
            for key in data.keys():
                if key.startswith('DefaultSettings:'):
                    item = data[key]
                    name = key[len('DefaultSettings:'):]
                    if not name:
                        raise ValueError('DefaultSettings section defined without a name in "%s"' %(fname,))
                    if name in self.defaultSettings:
                        raise KeyError('Multiple DefaultSettings object with name "%s". Second encountered in "%s"' %(name, fname))

                    self.defaultSettings[name] = item

        for i in range(len(self.datas)):
            data = self.datas[i]
            fname = self.filenames[i]
            for key in data.keys():
                if key.startswith('Program:'):
                    item = data[key]
                    name = key[len('Program:'):]
                    if 'defaults' in item:
                        defaultName = item['defaults']
                        if defaultName not in self.defaultSettings:
                            raise ValueError('Program "%s" in file "%s" uses a "defaults" of "%s", but no such DefaultSettings section exists in read configuration files!' %( name, fname, defaultName))
                        item2 = self.defaultSettings[defaultName]
                        item2 = copy.deepcopy(item2)
                        # Merge subsections if present
                        if 'Env' in item2 and 'Env' in item:
                            item2['Env'].update(item['Env'])
                            item['Env'] = item2['Env']
                            del item2['Env']
                        if 'Monitoring' in item2 and 'Monitoring' in item:
                            item2['Monitoring'].update(item['Monitoring'])
                            item['Monitoring'] = item2['Monitoring']
                            del item2['Monitoring']

                        item2.update(item)
                        item = item2

                    self.programConfigs[name] = ProgramConfig(name, **item)



    def getProgramConfig(self, programName):
        '''
            getProgramConfig - get the ProgramConfig associated with a program.

            @param programName <str> - Name of program

            @raises KeyError if program not found

            @return ProgramConfig of the program
        '''
        return self.programConfigs[programName]

    def getProgramConfigs(self):
        '''
            getProgramConfigs - Get all program configs.

            @return <dict> - program name <str> to ProgramConfig
        '''
        return self.programConfigs
