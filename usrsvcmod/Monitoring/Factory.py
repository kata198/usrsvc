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


    Kind of a psuedo-factory pattern for Monitoring. Not a regular factory because I want to be able to order priority, etc
'''

from . import MonitoringList
from .ActivityFile import ActivityFileMonitor
from .RSSLimit import RSSLimitMonitor

from ..logging import logErr


ALL_MONITORING_CLASSES = [ActivityFileMonitor, RSSLimitMonitor]


class MonitoringFactory(object):

    @staticmethod
    def getAsyncMonitorsForProgram(programConfig):
        '''
            getMonitorsForProgram - Gets any async monitors (runs inline in the main monitoring thread) for a given program.

            @param programConfig <usrsvcmod.ProgramConfig obj> - The ProgramConfig for this program

            @return - list<MonitoringBase> - A list of monitors in the order they should be tried for the given program, or empty list if all monitors are disabled.
        '''
        ret = MonitoringList()

        # Right now we will just do a list, but we may need more complicated ordering in the future
        for monitoringClass in ALL_MONITORING_CLASSES:
            try:
                monitoringObj = monitoringClass.createFromConfig(programConfig)
                if monitoringObj is None:
                    continue
                ret.append(monitoringObj)
            except Exception as e:
                logErr('EXCEPTION while generating Monitoring classes! Class was %s and program was %s. Error: %s\n' %(monitoringClass.__name__, programConfig.name, str(e)))

        return ret

