'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    'Program' represents a program, running or not.
'''

import os
import signal
import shlex
import subprocess
import time

__all__ = ('Program',)

class Program(object):


    def __init__(self, pidfile=None, pid=None, cmdline=None, executable=None, args=None, running=False):
        self.pid = pid or None
        # Note: careful with the cmdline/executable/args, maybe not all being set. Maybe need to ensure with a helper method.
        self.cmdline = cmdline or None
        self.executable = executable or None
        self.args = args or []
        self.running = running

        

    def isRunning(self):
        # TODO: get rid of this method
        return bool(self.running)

    @staticmethod
    def _getProcCmdline(pid):
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
        if forcePid is None:
            forcePid = self.pid
        if not forcePid:
            raise ValueError('Cannot call setCmdlineFromProc on a program without an associated pid.')

        cmdlineInfo = self._getProcCmdline(forcePid)

        self.cmdline = cmdlineInfo['cmdline']
        self.executable = cmdlineInfo['executable']
        self.args = cmdlineInfo['args']

    def validateProcTitle(self, programConfig):
        if not programConfig.proctitle_re:
            # Disabled proctitle matching somehow. So always match. BAD IDEA!
            return True

        return bool(programConfig.proctitle_re.search(self.cmdline))

    @classmethod
    def createFromPidFile(cls, pidfile):
        with open(pidfile, 'rt') as f:
            pid = f.read().strip()
        pid = int(pid)
        procCmdline = cls._getProcCmdline(pid)

        return cls(pidfile, pid, running=True, **procCmdline)

    @classmethod
    def createFromRunningProcesses(cls, programConfig):
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
        try:
            prog = cls.createFromPidFile(programConfig.pidfile)
        except:
            return False

        return prog.validateProcTitle(programConfig)


    def getStartTime(self):
        try:
            return os.stat('/proc/' + str(self.pid)).st_mtime
        except Exception as e:
            pass

        return None


    def startProgram(self, programConfig):
        useShell = programConfig.useshell

        if useShell is False:
            command = shlex.split(programConfig.command)
        else:
            command = programConfig.command

        success = True
        try:
            stdout = open(programConfig.stdout, 'at')
        except:
            raise ValueError('Cannot open %s for writing.' %(programConfig.stdout,))
        if programConfig.stdout == programConfig.stderr:
            stderr = stdout
        else:
            try:
                stderr = open(programConfig.stderr, 'at')
            except:
                raise ValueError('Cannot open %s for writing.' %(programConfig.stderr,))

        if programConfig.inherit_env:
            env = os.environ
        else:
            env = {}

        env.update(programConfig.Env)

        pipe = subprocess.Popen(command, shell=useShell, stdout=stdout, stderr=stderr, env=env)
        
        now = time.time()
        successAfter = now + programConfig.success_seconds

        pollTime = min(programConfig.success_seconds, .1)
        while time.time() < successAfter:
            time.sleep(pollTime)
            if pipe.poll() is not None:
                success = False
                break

        if success is False:
            # We've failed to restart after the given number of tries.
            return False

        # Started successfully, update our dict.
        self.pid = int(pipe.pid)
        try:
            self.setCmdlineFromProc()
        except:
            # Oh no! By some fluke, the program stopped running while we were setting it up. Return False....
            self.running = False
            return False

        self.running = True

        self.writePidFile(programConfig, self.pid)

        return True

    def writePidFile(self, programConfig, forcePid=None):
        if forcePid:
            pid = forcePid
        else:
            pid = self.pid

        if programConfig.autopid is False or not programConfig.pidfile:
            return False
        with open(programConfig.pidfile, 'wt') as f:
            f.write("%s\n" %(str(pid),))
        return True
        

    def removePidFile(self, programConfig):
        try:
            os.unlink(programConfig.pidfile)
            return True
        except:
            return False

    def stopProgram(self, programConfig):
        if self.pid and self.validateProcTitle(programConfig):
            try:
                os.kill(self.pid, signal.SIGTERM)
                termToKillSeconds = programConfig.term_to_kill_seconds
                now = time.time()
                maxTimeBeforeKill = now + termToKillSeconds

                pollTime = min(termToKillSeconds, .1)

                while now < maxTimeBeforeKill:
                    # If process has died, abort.
                    if not os.path.exists('/proc/%d' %(self.pid,)):
                        break
                    # Otherwise, wait 100ms before checking again.
                    time.sleep(pollTime)
                    now = time.time()

                # If program has not terminated given the threshold, send 'er the ol' boot.
                if now >= maxTimeBeforeKill:
                    os.kill(self.pid, signal.SIGKILL)
            except:
                pass

        # Remove pid file
        self.removePidFile(programConfig)
