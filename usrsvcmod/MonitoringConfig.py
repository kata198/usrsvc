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


    'MonitoringConfig' represents the monitoring subsection of a ProgramConfig
'''

from .configcommon import getConfigValueBool, getConfigValueInt, getConfigValueFloat

__all__ = ('MonitoringConfig',)

class MonitoringConfig(object):
    '''
        MonitoringConfig - The [[Monitor]] subsection of a Program
    '''

    def __init__(self, monitor_after=30,
        activityfile='', activityfile_limit=120,
        **kwargs):
        '''
            Config values:

            monitor_after - Minimum number of seconds that program needs to be running before monitoring will begin. Default 30. 0 disables this feature.
            activityfile - File or Directory which must be modified every #activityfile_limit# seconds, or program will be restarted. Default undefined/empty string disables this.
            activityfile_limit - If activityfile is defined, this is the number of seconds is the maximum that can go between modifications of the provided #activityfile# before triggering a restart.
        '''

        self.monitor_after = getConfigValueInt(monitor_after, 'monitor_after')

        self.activityfile = activityfile
        if activityfile and activityfile[0] != '/':
            raise ValueError('activityfile must be an absolute path.\n')
        self.activityfile_limit = getConfigValueInt(activityfile_limit, 'activityfile_limit')
        if kwargs:
            raise ValueError('Unknown configuration options in Monitoring section: %s' %(str(kwargs.keys()),))


    def isMonitoringActive(self):
        # "or" of all the various monitoring types.
        return bool(self.activityfile)

        
    def __str__(self):
        return str(self.__dict__)
