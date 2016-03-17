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


    Monitoring Stuff
'''

import time

from ..logging import logErr

__all__ = ('MonitoringBase', 'MonitoringList')

# TODO: Some monitoring will need to run as a separate thread and this base class should provide the means to launch and then later join and assert.
class MonitoringBase(object):
    '''
        MonitoringBase - A base class for monitoring. Right now mostly just a placeholder,
            but will be used when more advanced monitors are created.
    '''


    @classmethod
    def createFromConfig(cls, programConfig):
        '''
            createFromConfig - Create an instance of the monitoring class from the given config. Return None if this monitor is inactive for this program.

            @param programConfig <usrsvcmod.ProgramConfig>   - The ProgramConfig for a given program.

            @return <None/object> - None if the monitor is disabled, otherwise an instance of the monitoring class with all config values set.
        '''
        raise NotImplementedError('Monitor %s does not implement createFromConfig.' %(str(cls.__name__), ))

    def shouldRestart(self, program):
        '''
            shouldRestart - Run the test, and check if we should restart the app.

            @param program <usrsvcmod.Program> - The Program instance representing the running program being monitored. May not be required for all checks

            @return <bool> - True if we should trigger a restart.
        '''
        return False


class MonitoringList(list):
    '''
        MonitoringList - A list of monitors. Has functions to simplify common usage
    '''

    def executeList(self, program):
        '''
            executeList - Runs the monitors in order until all have been completed or one fails.

            @param program <usrsvcmod.Program> - The Program instance representing the Program to monitor

            @return <dict> - {
                'doRestart' : <bool> - True if we should trigger a restart, otherwise False.
                'triggeredAlert' : <None/object> - The object of the monitor that triggered
                'runtime' : <float> - The time it took to run the monitors
                'numRan'  : <int> - The number of monitors that ran
            }
        '''
        ret = {
            'doRestart' : False,
            'triggeredAlert' : None,
            'runtime' : time.time(),
            'numRan' : 0
        }

        shouldRestart = False
        for mon in self:
            ret['numRan'] += 1
            try:
                shouldRestart = mon.shouldRestart(program)
                if shouldRestart is True:
                    break
            except Exception as e: 
                logErr('Unexpected exception when running list of monitors: %s.\nLocals: %s\nMoving on..\n' %(str(e), str(locals())))
                continue

        if shouldRestart is True:
            ret['triggeredAlert'] = mon
            ret['doRestart'] = True

        ret['runtime'] = time.time() - ret['runtime']

        return ret
                
