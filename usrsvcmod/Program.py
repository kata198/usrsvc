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

# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :

import os
import signal
import shlex
import subprocess
import re
import time
import traceback

from .constants import ReturnCodes
from .logging import logMsg, logErr
from .util import  waitUpTo
from usrsvcmod.debug import isDebugEnabled

__all__ = ('Program',)

STAT_PATTERN = re.compile('^(?P<pid>[\d]+)[ ][\(](?P<cwd>.+)[\)][ ](?P<state>[^ ]+)[ ](?P<ppid>[\d]+)[ ](?P<unparsed>.*)$')

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
        cmdlineContents = b''
        with open('/proc/%d/cmdline' %(pid,), 'rb') as f:
            cmdlineContents = f.read()

        if not cmdlineContents:
            raise KeyError('Process pid=%d has empty cmdline' %(pid,))
        
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
    def getStatInfo(cls, pid):
        '''
            getStatInfo - Parses /proc/$PID/stat and returns a dict of contents.

            Dict is not complete, all members currently needed are present, everything else will be in "unparsed"

            @return <dict> - Dict of stat fields. Current supported keys are:
                pid - Process ID of this process
                cwd - Current working directory of process
                state - State code
                ppid  - Parent Pid

            @raises - KeyError if process does not exist
                      ValueError if stat file cannto be parsed
        '''
        statFilename = '/proc/%d/stat' %(int(pid),)
        try:
            with open(statFilename, 'rt') as f:
                contents = f.read()
        except Exception as e:
            raise KeyError('Cannot read stat file "%s" : %s' %(statFilename, str(e)))

        statInfo = STAT_PATTERN.match(contents)
        if not statInfo:
            raise ValueError('Could not parse stat file, "%s"' %(statFilename, ))

        groupDict = statInfo.groupdict()
        groupDict['pid'] = int(groupDict['pid'])
        groupDict['ppid'] = int(groupDict['ppid'])
        return groupDict

    @classmethod
    def getChildPids(cls, pid):
        '''
            getChildPids - Get pids of children of a given process.

            Note -- this is on the order of 100x faster than using psutil, so that's why it's reimplemented.

            @param pid <int> - A process pid

            @return list<int> - List of children pids
        '''
        myPids = cls.getMyRunningPids()
        pid = int(pid)

        childPids = []

        for myPid in myPids:
            try:
                statInfo = cls.getStatInfo(myPid)
            except:
                continue
            if pid == statInfo['ppid']:
                childPids.append(myPid)

        return childPids

    @classmethod
    def getAllChildPidsInTree(cls, rootPid):
        '''
            getAllChildPidsInTree - Get pids of children of given process, and their children, and their children...

            @param rootPid <int> - A process pid

            @return list<int> - Flat list of all child pids and their children.
        '''
        childPids = Program.getChildPids(rootPid)
        if not childPids:
            return []

        # Get children of all children as well
        newChildPids = childPids[:]
        while newChildPids:
            newChildPids2 = []
            for newChildPid in newChildPids:
                childChildPids = Program.getChildPids(newChildPid)
                if isDebugEnabled() and childChildPids:
                    logMsg('DEBUG: Add child-of-child %d pids: %s\n' %(newChildPid, str(childChildPids)))
                newChildPids2 += childChildPids
                childPids += childChildPids
            newChildPids = newChildPids2

        return childPids

    @classmethod
    def getParentPid(cls, pid):
        '''
            getParentPid - Get parent pid of given process pid.

            @param pid <int> - Process pid

            @return <int/None> - Integer of parent pid of @pid, or None if could not determine (like program not running)
        '''
        pid = int(pid)
        try:
            statInfo = cls.getStatInfo(pid)
        except:
            return None

        return statInfo['ppid']


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
    def getMyRunningPids(cls):
        '''
            getMyRunningPids - Get all running pids which are owned by the current user.

            @return - List of all running pids.

            When iterating, you likely want to wrap in try/except incase the pid stops running.
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

        return allMyPids

    @classmethod
    def createFromRunningProcesses(cls, programConfig):
        '''
            createFromRunningProcesses - Create a Program using programConfig. scans all running processes, and returns a constructed Program if a match is found.

            @param programConfig <ProgramConfig.ProgramConfig> - The config for a program

            @return - A constructed "Program" if a match found, ootherwise None.

            Should not raise anything.
        '''
        allMyPids = cls.getMyRunningPids()

        proctitleRE = programConfig.proctitle_re

        for pid in allMyPids:
            try:
                # Do in a loop incase processes are created/destroyed between getting the list and checking it
                procCmdline = cls._getProcCmdline(pid)

                # Make sure we match actual process and not the wrapping shell.
                if programConfig.useshell is True and procCmdline['cmdline'].startswith('/bin/sh -c'):
                    continue
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
            return ReturnCodes.INSUFFICIENT_PERMISSIONS
#            raise ValueError('Cannot open %s for writing.' %(programConfig.stdout,))
        if programConfig.stdout == programConfig.stderr:
            stderr = stdout
        else:
            try:
                stderr = open(programConfig.stderr, 'at')
            except Exception as e:
                logErr('(%s) - Cannot open stderr %s for writing: %s\n' %(programConfig.name, programConfig.stderr, str(e)))
                return ReturnCodes.INSUFFICIENT_PERMISSIONS
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
        
        time.sleep(.1) # Give a chance to start program
        now = time.time()
        successAfter = now + programConfig.success_seconds

        success = True

        # Ensure we poll at least 5 times
        pollTime = min(programConfig.success_seconds / 5.0, .1)

        if success is False:
            # We've failed to restart after the given number of tries.
            return ReturnCodes.PROGRAM_EXITED_UNEXPECTEDLY

        # Check if useshell is True, but we didn't actually use one.
        if useShell is True:
            cmdline = None
            try:
                cmdline = self._getProcCmdline(pipe.pid)
            except:
                # Program died, we will catch below.
                pass
            if cmdline is not None and not cmdline['cmdline'].startswith('/bin/sh -c'):
                logMsg('%s - useshell is set to True, but program does not require a shell parent. Resetting useShell to False.\n' %(programConfig.name,))
                programConfig.use_shell = useShell = False
                useShell = False

        # Started successfully, update our dict.
        # If they are using shell, we don't want to match the shell subprocess. So search child processes until we find it.
        rootPid = int(pipe.pid)
        firstChildIsProcess = False
        foundMatchingChild = False

        if useShell is False:
            try:
                cmdline = self._getProcCmdline(rootPid)
            except:
                # Program died, we will catch below.
                pass
            if cmdline is not None and bool(programConfig.proctitle_re.search(cmdline['cmdline'])):
                if isDebugEnabled():
                    logMsg('DEBUG: first child is process\n' )
                firstChildIsProcess = True
                foundMatchingChild = True
                self.pid = rootPid

        
        while time.time() < successAfter:
            pollResult = pipe.poll()
            if pollResult is not None:
                if useShell is True:
                    whatExited = "shell"
                else:
                    whatExited = "process"
                logErr('(%s) - Parent %s exited with code=%d\n' %(programConfig.name, whatExited, pollResult))
                return ReturnCodes.PROGRAM_FAILED_TO_LAUNCH

            if firstChildIsProcess is True:
                continue

            if isDebugEnabled():
                logMsg('DEBUG: Checking for child pids of %d\n' %(rootPid,))

            childPids = Program.getAllChildPidsInTree(rootPid)
            if childPids:
                if isDebugEnabled():
                    logMsg('DEBUG: Found children of %d: %s\n' %(rootPid, str(childPids),))
                for childPid in childPids:
                    try:
                        cmdline = self._getProcCmdline(childPid)
                        if isDebugEnabled():
                            logMsg('DEBUG: Checking child pid=%d %s...\n' %(childPid, cmdline['cmdline']))
                        if cmdline['cmdline'] and not cmdline['cmdline'].startswith('/bin/sh -c') and bool(programConfig.proctitle_re.search(cmdline['cmdline'])):
                            if isDebugEnabled():
                                logMsg('DEBUG Matched child!\n')
                            self.pid = childPid
                            foundMatchingChild = True
                            break
                    except Exception as e:
                        if isDebugEnabled():
                            logErr('Error checking child pid=%d: %s\n' %(childPid, str(e),))
                            traceback.print_exc()

                if foundMatchingChild is True:
                    while time.time() < successAfter:
                        time.sleep(pollTime)
                        if not os.path.exists('/proc/%d' %(self.pid,)):
                            logMsg('Found child process pid=%d cmdline=%s, but it stopped running. Checking other children...\n' %(self.pid, str(cmdline)))
                            self.pid = None
                            foundMatchingChild = False
                            break
                    if foundMatchingChild is True:
                        break

            time.sleep(pollTime)
        
        if foundMatchingChild is False:
            logErr('(%s) - Failed to find program matching proctitle_re. Shell pid is: %d\n' %(programConfig.name, pipe.pid))
            return ReturnCodes.PROGRAM_FAILED_TO_LAUNCH

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
                processDied = waitUpTo(os.path.exists, ('/proc/%d' %(self.pid,) , ), timeout=termToKillSeconds, interval=pollInterval)
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


# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :
