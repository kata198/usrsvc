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


    ActivityFileMonitor - Asserts that a specific file or directory should be modified within a certain threshold
'''

import os
import time

from func_timeout import FunctionTimedOut

from . import MonitoringBase
from ..logging import logMsg, logErr

# TODO: We need to implement the check here as launching and joining on a thread, so that we don't lockup all monitoring if someone
#  uses an NFS file on a disconnected device or anything else that will result in an indefinite uninterruptable ("D") state.

class ActivityFileMonitor(MonitoringBase):
    '''
        ActivityFileMonitor - Class for doing activity file monitoring
    '''

    def __init__(self, programName, activityFile, activityFileLimit):
        self.programName = programName
        self.activityFile = activityFile
        self.activityFileLimit = activityFileLimit

    @classmethod
    def createFromConfig(cls, programConfig):
        if not programConfig.Monitoring.activityfile:
            return None

        return cls(programConfig.name, programConfig.Monitoring.activityfile, programConfig.Monitoring.activityfile_limit)

    def shouldRestart(self, program=None):
        '''
            Returns True if activity file has not been modified within the threshold specified by activityfile_limit (should restart), otherwise False.

            @param program - unused.
        '''
        activityFile = self.activityFile
        activityFileLimit = self.activityFileLimit
        programName = self.programName

        if not activityFile:
            # Yes this is checked twice if created through createFromConfig, but it may be called otherwise so better safe.
            return False

        try:
            # If activity file is not present, this is a fail and we restart.
            if not os.path.exists(activityFile):
                logMsg('Restarting %s because activity file ( %s ) does not exist\n' %(programName, activityFile,))
                return True
            # Gather the mtime and see if we are past the threshold
            lastModified = os.stat(activityFile).st_mtime
            threshold = float(time.time() - self.activityFileLimit)
            if lastModified < threshold:
                logMsg('Restarting %s because it has not modified activity file ( %s ) in %.4f seconds. Limit is %d.\n' %(programName, activityFile, float(threshold - lastModified), activityFileLimit))
                return True
        except FunctionTimedOut:
            logErr('MONITOR: ActivityFile timed out on %s\n' %(programName,))
            raise

        except Exception as e:
            # If we got an exception, just log and try again next round.
            logErr('Got an exception in activity file monitoring. Not restarting program. Program="%s" activityfile="%s"\nlocals: %s\n' %(programName, activityFile, str(locals())))

        return False 


