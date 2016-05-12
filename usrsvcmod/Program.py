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


    'Program' represents a program, running or not.
'''

import os
import signal
import shlex
import subprocess
import time

from .constants import ReturnCodes
from .logging import logMsg, logErr
from .util import  waitUpTo

__all__ = ('Program',)

class Program(object):
    '''
        Program - defines a program, running or not.
    '''


    def __init__(self, pidfile=None, pid=None, cmdline=None, executable=None, args=None, running=False):
        '''
            Create a program.

            @param pidfile - <str/None> - path to pidfile
            @param pid - <int/None> - pid of program
            @param cmdline - <str/None> - cmdline of program
            @param executable - <str/None> - executable or None
            @param args - <list/None> - List of args, or None.
            @param running - <bool> - True/False.

            Should not be created direcly, use one of the static methods to create this.
        '''
        self.pid = pid or None
        # Note: careful with the cmdline/executable/args, maybe not all being set. Maybe need to ensure with a helper method.
        self.cmdline = cmdline or None
        self.executable = executable or None
        self.args = args or []
        self.running = running

        
    @staticmethod
    def _getProcCmdline(pid):
        '''
            _getProcCmdline - Gets the /proc/$pid/cmdline , split into string, executable, and args, for a given pid.

            @return - dict {
                cmdline - string of commandline
                executable - string of executable
                args - list of arguments
                }

        '''
        with open('/proc/%d/cmdline' %(pid,), 'rb') as f:
            cmdlineContents = f.read()
        
        # Split by null, and strip the trailing null
        cmdlineSplit = cmdlineContents.split(b'\x00')[:-1]
        executable = cmdlineSplit[0].decode('utf-8')
        args = [x.decode('utf-8') for x in cmdlineSplit[1:]]

        cmdline = ' '.join([executable] + args)

        return {
            'cmdline' : cmdline,
            'executable' : executable,
            'args' : args
        }

    def setCmdlineFromProc(self, forcePid=None):
        '''
            setCmdlineFromProc - Sets the commandline properties (cmdline, exectuable, args) from the proc value.

            @param forcePid - Uses the pid on this object as default, but you can force another with this param.

        '''
        if forcePid is None:
            forcePid = self.pid
        if not forcePid:
            raise ValueError('Cannot call setCmdlineFromProc on a program without an associated pid.')

        cmdlineInfo = self._getProcCmdline(forcePid)

        self.cmdline = cmdlineInfo['cmdline']
        self.executable = cmdlineInfo['executable']
        self.args = cmdlineInfo['args']

    def validateProcTitle(self, programConfig):
        '''
            validateProcTitle - uses proctitle_re to validate if the proctitle associated with the pid associated with this object
              matches.

            @return -<bool> If the pid associated with this Program has a proctitle that matches
        '''
        if not programConfig.proctitle_re:
            # Disabled proctitle matching somehow. So always match. BAD IDEA!
            return True

        return bool(programConfig.proctitle_re.search(self.cmdline))

    @classmethod
    def createFromPidFile(cls, pidfile):
        '''
            createFromPidFile - Creates a Program from a pidfile.

            @param pidfile <str> - Path to pid file

            @raises - An exception if no process can be created from the pidfile. Specific exception depends on error. Not validated with proctitle_re, do that in an additional call.
        '''
        with open(pidfile, 'rt') as f:
            pid = f.read().strip()
        pid = int(pid)
        procCmdline = cls._getProcCmdline(pid)

        return cls(pidfile, pid, running=True, **procCmdline)

    @classmethod
    def createFromRunningProcesses(cls, programConfig):
        '''
            createFromRunningProcesses - Create a Program using programConfig. scans all running processes, and returns a constructed Program if a match is found.

            @param programConfig <ProgramConfig.ProgramConfig> - The config for a program

            @return - A constructed "Program" if a match found, ootherwise None.

            Should not raise anything.
        '''
        myUid = os.getuid()
        allMyPids = []
        # Do in a loop incase processes are created/destroyed between getting the list and checking it
        for procItem in os.listdir('/proc'):
            try:
                if procItem.isdigit() and os.stat('/proc/' + procItem).st_uid == myUid:
                    allMyPids.append(int(procItem))
            except:
                pass

        proctitleRE = programConfig.proctitle_re

        for pid in allMyPids:
            try:
                # Do in a loop incase processes are created/destroyed between getting the list and checking it
                procCmdline = cls._getProcCmdline(pid)
                if bool(proctitleRE.search(procCmdline['cmdline'])):
                    prog = cls(programConfig.pidfile, pid, running=True, **procCmdline)
                    return prog
            except:
                pass

        return None
                    

    @classmethod
    def isProgramRunning(cls, programConfig):
        '''
            isProgramRunning - Actively check if a program is running

            @param programConfig <ProgramConfig.ProgramConfig> - The config of a program

            @return - True if the program is running and matches the proctitle.

            NOT USED!

            Use ProgramActions.getRunningProgram instead. That will return the program itself, and manage the pidfile.

        '''
        prog = None
        try:
            prog = cls.createFromPidFile(programConfig.pidfile)
        except:
            pass

        if prog is None and programConfig.scan_for_process is True:
            try:
                prog = Program.createFromRunningProcesses(programConfig)
                return True # Don't need to re-validate the proc title
            except:
                return False

        if prog is None:
            return False

        return prog.validateProcTitle(programConfig)


    def getStartTime(self):
        '''
            getStartTime - Get the epoch timestamp for when this process was started.

            @return - time process was started, or None if no program found matching this Program's pid.
        '''
        try:
            statInfo = os.stat('/proc/' + str(self.pid))
            if not statInfo:
                return None
            # Try ctime first, but may not be present everywhere, so fallback to st_mtime
            if hasattr(statInfo, 'st_ctime') and statInfo.st_ctime:
                return statInfo.st_ctime
            return statInfo.st_mtime
        except Exception:
            pass

        return None


    def startProgram(self, programConfig):
        '''
            startProgram - Start the program and update this object.

            @param programConfig <ProgramConfig.ProgramConfig> - The program config associated with this program.
        '''
        useShell = programConfig.useshell

        if useShell is False:
            command = shlex.split(programConfig.command)
        else:
            command = programConfig.command

        try:
            stdout = open(programConfig.stdout, 'at')
        except Exception as e:
            logErr('(%s) - Cannot open stdout %s for writing: %s\n' %(programConfig.name, programConfig.stdout, str(e)))
            return ReturnCodes.INSUFFICENT_PERMISSIONS
#            raise ValueError('Cannot open %s for writing.' %(programConfig.stdout,))
        if programConfig.stdout == programConfig.stderr:
            stderr = stdout
        else:
            try:
                stderr = open(programConfig.stderr, 'at')
            except Exception as e:
                logErr('(%s) - Cannot open stderr %s for writing: %s\n' %(programConfig.name, programConfig.stderr, str(e)))
                return ReturnCodes.INSUFFICENT_PERMISSIONS
#                raise ValueError('Cannot open %s for writing.' %(programConfig.stderr,))

        if programConfig.inherit_env:
            env = os.environ
        else:
            env = {}

        if hasattr(subprocess, 'DEVNULL'):
            devnull = subprocess.DEVNULL
        else:
            devnull = open('/dev/null', 'rt')

        env.update(programConfig.Env)

        try:
            pipe = subprocess.Popen(command, shell=useShell, stdout=stdout, stderr=stderr, stdin=devnull, env=env, close_fds=False)
        except Exception as e:
            logErr('(%s) - Failed to run command ( %s ): %s\n' %(programConfig.name, str(command), str(e)))
            return ReturnCodes.PROGRAM_FAILED_TO_LAUNCH
        
        now = time.time()
        successAfter = now + programConfig.success_seconds

        success = True

        pollTime = min(programConfig.success_seconds, .1)
        while time.time() < successAfter:
            time.sleep(pollTime)
            pollResult = pipe.poll()
            if pollResult is not None:
                logErr('(%s) - Exited with code=%d\n' %(programConfig.name, pollResult))
                success = False
                break

        if success is False:
            # We've failed to restart after the given number of tries.
            return ReturnCodes.PROGRAM_EXITED_UNEXPECTEDLY

        # Started successfully, update our dict.
        self.pid = int(pipe.pid)
        try:
            self.setCmdlineFromProc()
        except:
            # Oh no! By some fluke, the program stopped running while we were setting it up. Return False....
            self.running = False
            return ReturnCodes.PROGRAM_EXITED_UNEXPECTEDLY

        self.running = True

        self.writePidFile(programConfig, self.pid)

        return ReturnCodes.SUCCESS


    def stopProgram(self, programConfig):
        '''
            stopProgram - Stop this Program and remove pid file.

            @param programConfig <ProgramConfig.ProgramConfig> - The ProgramConfig for this program

            @return <str> - Returns a string of what happened. Can be one of "noaction", "terminated" (SIGTERM), "killed" (SIGKILL)

        '''

        result = 'no action'

        if self.pid and self.validateProcTitle(programConfig):
            try:
                os.kill(self.pid, signal.SIGTERM)
                result = 'terminated'

                termToKillSeconds = programConfig.term_to_kill_seconds

                pollInterval = min(termToKillSeconds / 10.0, .1)
                processDied = waitUpTo(os.path.exists, '/proc/%d' %(self.pid,), timeout=termToKillSeconds, interval=pollInterval)
                if processDied is False:
                    # If program has not terminated given the threshold, send 'er the ol' boot.
                    os.kill(self.pid, signal.SIGKILL)
                    result = 'killed'

            except:
                pass

        # Remove pid file
        self.removePidFile(programConfig)

        return result


    def writePidFile(self, programConfig, forcePid=None):
        '''
            writePidFile - write the pid file for this program.

            @param programConfig <ProgramConfig.ProgramConfig> - The ProgramConfig for this program
            
            @param forcePid <int/None> - if provided, use this pid instead of self.pid

            @return - False if not written (no autopid), otherwise True if written.
        '''
        if forcePid:
            pid = forcePid
        else:
            pid = self.pid

        # Note: pidfile should never be undefined... but just incase somehow.
        if programConfig.autopid is False or not programConfig.pidfile:
            return False
        with open(programConfig.pidfile, 'wt') as f:
            f.write("%s\n" %(str(pid),))
        return True
        

    def removePidFile(self, programConfig):
        '''
            removePidFile - Removes the pid file associated with this Program.

            @param programConfig <ProgramConfig.ProgramConfig> - The ProgramConfig for this program
        '''

        try:
            if os.path.exists(programConfig.pidfile):
                os.unlink(programConfig.pidfile)
            return True
        except Exception as e:
            if os.path.exists(programConfig.pidfile):
                # Check again incase something else removed it, we only want to alert when we couldn't remove it.
                logErr('(%s) Unable to remove pidfile %s: %s\n' %(programConfig.name, programConfig.pidfile, str(e)))
            return False

    def __str__(self):
        return str(self.__dict__)
