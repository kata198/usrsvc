'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    'MonitoringConfig' represents the monitoring subsection of a ProgramConfig
'''

from .configcommon import getConfigValueBool, getConfigValueInt, getConfigValueFloat

__all__ = ('MonitoringConfig',)

class MonitoringConfig(object):

    def __init__(self, activityfile='', activityfile_limit=15, **kwargs):
        self.activityfile = activityfile
        if activityfile and activityfile[0] != '/':
            raise ValueError('activityfile must be an absolute path.\n')
        self.activityfile_limit = getConfigValueInt(activityfile_limit, 'activityfile_limit')
        if kwargs:
            raise ValueError('Unknown configuration options in Monitoring section: %s' %(str(kwargs.keys()),))

        
    def __str__(self):
        return str(self.__dict__)
