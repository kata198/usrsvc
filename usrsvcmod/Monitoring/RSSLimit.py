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


    RSSLimitMonitor - Monitor maximum RSS (Resident Set Size)
'''

from func_timeout import FunctionTimedOut

from . import MonitoringBase
from ..logging import logMsg, logErr



try:
    import resource
    PAGE_SIZE = resource.getpagesize()
except:
    # Fallback if resource is not available, assume 4096.
    PAGE_SIZE = 4096

class RSSLimitMonitor(MonitoringBase):
    '''
       RSSLimitMonitor - Class for monitoring RSS
    '''

    def __init__(self, programName, rssLimit):
        '''
            @param programName <str> - Name of program
            @param rssLimit <int> - kB maximum RSS size
        '''
        self.programName = programName
        self.rssLimit = rssLimit

    @classmethod
    def createFromConfig(cls, programConfig):
        if not programConfig.Monitoring.rss_limit:
            return None

        return cls(programConfig.name, programConfig.Monitoring.rss_limit)

    def shouldRestart(self, program):
        rssLimit = self.rssLimit

        if rssLimit <= 0:
            # Yes this is checked twice if created through createFromConfig, but it may be called otherwise so better safe.
            return False

        try:
            with open('/proc/%d/statm' %(program.pid,), 'rt') as f:
                contents = f.read()
            fields = contents.split()
            rssPages = int(fields[1])
            rssKB = int((rssPages * PAGE_SIZE) / 1024)
            if rssKB > self.rssLimit:
                logMsg('Restarting %s because RSS size %dkB exceeds limit of %dkB' %(self.programName, rssKB, rssLimit))
                return True
        except FunctionTimedOut:
            logErr('MONITOR: RSSLimit timed out on %s\n' %(self.programName,))
            raise
        except Exception as e:
            # If we got an exception, just log and try again next round.
            logErr('Got an exception in RSS monitoring. Not restarting program. Program="%s"\n%s\nlocals: %s\n' %(self.programName, str(program), str(locals())))

        return False 


