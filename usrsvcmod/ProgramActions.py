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


    ProgramActions - Some common actions dealing with process management.
'''

from .Program import Program
from .logging import logErr, logMsg

# TODO: Notification system

def getRunningProgram(programConfig):
    '''
        getRunningProgram - Get a "Program" object representing a running program, or None if not running.

            Also handles validating proctitle and removing stale pid files.

            Tries pidfile first, if no match then if scan_for_process is set on the programConfig, running processes will
              be scanned and if a proctitle match is found, a pidfile wiil be written and the program returned.

         @param programConfig <ProgramConfig obj> - The ProgramConfig object representing the program to fetch.

         @return <None/Program> - A running Program if match was found, otherwise None.
    '''
    programName = programConfig.name

    prog = None
    try:
        # Try to get program from pidfile
        prog = Program.createFromPidFile(programConfig.pidfile)
    except:
        pass

    if prog is not None:
        # A program is running, check if it is the RIGHT program
        isCorrectApp = prog.validateProcTitle(programConfig)
        if not isCorrectApp:
            logErr('Warning: Detected stale pid file for %s at %s (%d). REMOVING\n  Proctitle for %d was: %s\n' %(programName, programConfig.pidfile, prog.pid, prog.pid, prog.cmdline))
            prog.removePidFile(programConfig)
            prog = None
        else:
            # Program is running, and matched proctitle
            return prog
            
    if prog is None:
        if programConfig.scan_for_process is True:
            # No PID or failed proctitle match, scan running processes
            prog = Program.createFromRunningProcesses(programConfig)
            if prog:
                logMsg('Matched %s from running process:\n\n%s\n' %(programName, prog.__dict__))
                prog.writePidFile(programConfig)
                return prog

    return prog
