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

    usrsvc is the tool to start/stop/restart and get status on services. usrsvcd is the daemon for autostart, autorestart, monitoring, etc.
'''

# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :


import os
import copy
import signal
import multiprocessing
import sys
import traceback

from NamedAtomicLock import NamedAtomicLock

from usrsvcmod.UsrsvcConfig import UsrsvcConfig
from usrsvcmod.Program import Program
from usrsvcmod.ProgramActions import getRunningProgram
from usrsvcmod.logging import logMsg, logErr
from usrsvcmod.constants import ReturnCodes

class Usrsvc(object):

    def __init__(self, config=None):
        if not config:
            config = UsrsvcConfig(os.environ['HOME'] + '/usrsvc.cfg')
            try:
                config.parse()
            except ValueError as e:
                sys.stderr.write('ERROR in config: %s\n'  %(str(e),))
                raise e

        self.config = config

    def call(self, args):
        argv = args[:]
        if argv[0] != 'usrsvc':
            argv = ['usrsvc'] + args

        process = multiprocessing.Process(target=self._call_main, args=(argv,))
        process.start()

        return process

    def _call_main(self, argv):
        sys.exit(self.main(argv))

    def doActionParallel(self, action):
        config = self.config

        allProgramNames = config.getProgramConfigs().keys()
        processes = {}
        for programName in allProgramNames:
            process = multiprocessing.Process(target=self.doActionAndExit, args=([action, programName], ))
            process.start()
            processes[programName] = process

        ret = ReturnCodes.SUCCESS
        exitCodes = {}
        for processName, process in processes.items():
            process.join()
            exitCodes[processName] = process.exitcode

        for programName, exitCode in exitCodes.items():
            if exitCode != ReturnCodes.SUCCESS:
                ret = ReturnCodes.GENERAL_FAILURE
                logErr('%s exited with non-zero return code: %d (%s)\n' %(programName, exitCode, ReturnCodes.returnCodeToString(exitCode)) )

        return ret

    def doAction(self, args):
        config = self.config

        action = args[0]
        if args[1] == 'all':
            # Serial start, parallel is handled elsewhere
            ret = 0
            for programName in config.getProgramConfigs().keys():
                try:
                    exitCode = self.doAction([action, programName])
                except Exception as e:
                    logErr('Unexpected exception (%s) trying to %s %s: %s\n' %(str(e.__class__.__name__), action, programName, str(e)))
                    traceback.print_exc()
                    exitCode = ReturnCodes.UNKNOWN_FAILURE
                if exitCode != 0:
                    logErr('%s failed to %s with error %d (%s)\n' %(programName, action, exitCode, ReturnCodes.returnCodeToString(exitCode)) )
                    ret = ReturnCodes.GENERAL_FAILURE
            return ret
        
        programName = args[1]

        lock = NamedAtomicLock('.lock_usrsvc' + programName, maxLockAge=30)
        if not lock.acquire(31):
            logErr('Cannot acquire lock for %s. Is something else looping trying to access it? Try the command again.\n' %(programName,))
            return ReturnCodes.TRY_AGAIN
        ret = self._doAction(args)
        lock.release()
        return ret

    def _doAction(self, args):
        config = self.config

        action = args[0]
        programName = args[1]

        try:
            programConfig = config.getProgramConfig(programName)
        except KeyError:
            logErr('No such program: %s\n' %(programName,))
            return ReturnCodes.PROGRAM_UNDEFINED

        if programConfig.enabled is False and action != 'status':
            logErr('Program %s is currently disabled in config. Only the "status" action is supported on disabled programs.\n' %(programName,))
            return ReturnCodes.PROGRAM_DISABLED

        if action == 'start':
            prog = None
            try:
                prog = Program.createFromPidFile(programConfig.pidfile)
            except:
                pass

            prog = getRunningProgram(programConfig)
            if prog is not None:
                logMsg('Program %s is already running:\n\n%s\n' %(programName, prog.__dict__))
                return ReturnCodes.SUCCESS

            prog = Program(programConfig.pidfile)
            returnCode = prog.startProgram(programConfig)
            
            if returnCode == ReturnCodes.SUCCESS:
                logMsg('Started %s:\n\n%s\n' %(programName, prog.__dict__))
                return ReturnCodes.SUCCESS
            else:
                logErr('Failed to start %s! Err=%d (%s)\n' %(programName, returnCode, ReturnCodes.returnCodeToString(returnCode)))
                return returnCode

        elif action == 'stop':
            
            prog = getRunningProgram(programConfig)
            if prog:
                logMsg('Stopping %s [%d]\n' %(programName, prog.pid))
                actionTaken = prog.stopProgram(programConfig)
                logMsg('%s %s\n' %(programName, actionTaken))
            else:
                logMsg('%s was not running.\n' %(programName,))
            return ReturnCodes.SUCCESS
        elif action == 'restart':
            self._doAction(['stop'] + args[1:])
            return self._doAction(['start'] + args[1:])
        elif action == 'status':
            prog = getRunningProgram(programConfig)
            if prog:
                logMsg('%s is running:\n\n%s\n' %(programName, str(prog.__dict__)))
                return ReturnCodes.SUCCESS
            else:
                logErr('%s is NOT running\n' %(programName,))
                return ReturnCodes.GENERAL_FAILURE
        else:
            logErr('Unknown action: %s\n' %(action,))
            return ReturnCodes.INVALID_ACTION
     

    def doActionAndExit(self, args):
        sys.exit(self.doAction(args))


    @classmethod
    def printUsage(cls):
        sys.stderr.write('''Usage: usrsvc (Options) [start/stop/restart/status] [program name]
 Performs the requested action on the given program name.
 "all" can be used for start/stop/restart in place of "program name"
 
usrsvc is tool for performing specific actions on services, usrsvcd is the related daemon for autorestart/monitoring, etc.

  Options:
  --------

    Parallel:
        When doing start/stop/restart all, you may add "--parallel" or "-P" to perform 
        the action on all items in parallel.
          

  Config:
  -------

    Usrsvc uses the config file found at $HOME/usrsvc.cfg (%s).

  Documentation
  -------------

    Run "usrsvc --readme" or see https://github.com/kata198/usrsvc/blob/master/README.md 
      for more documentation.

''' %(os.environ['HOME'] + '/usrsvc.cfg', ) )

    
    def main(self, argv):
        parallelAll = False
        try:

            if '--help' in argv:
                self.printUsage()
                return ReturnCodes.HELP_MESSAGE
            elif '--readme' in argv:
                from usrsvcmod.client.readme import printReadme
                printReadme(sys.stdout)
                return ReturnCodes.HELP_MESSAGE
            elif len(argv) == 4 and argv[1] in ('start', 'stop', 'restart') and argv[2] == 'all' and (argv[3] == '--parallel' or argv[3] == '-P'):
                parallelAll = True
            elif len(argv) != 3:
                logErr('Invalid number of arguments.\n')
                self.printUsage()
                return ReturnCodes.GENERAL_FAILURE

            # Prevent signals from interrupting us
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)

            if parallelAll is True:
                return self.doActionParallel(argv[1])
            else:
                return self.doAction(argv[1:])

        except Exception  as  e:
           logErr('Error  in main %s:  %s\n'  %(str(argv), str(e)))
           return ReturnCodes.UNKNOWN_FAILURE



# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :
