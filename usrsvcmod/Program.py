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
        allMyPids = [int(x) for x in os.listdir('/proc') if x.isdigit() and os.stat('/proc/' + x).st_uid == myUid]

        proctitleRE = programConfig.proctitle_re

        for pid in allMyPids:
            try:
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


    def startProgram(self, programConfig):
        # TODO: Lock.
        numRestarts = programConfig.numrestarts + 1
        useShell = programConfig.useshell

        if useShell is False:
            command = shlex.split(programConfig.command)
        else:
            command = programConfig.command

        success = False
        for i in range(numRestarts):
            # TODO: redirect stderr and stdout
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
            # TODO: Loop on a smaller value to catch failure earlier
            time.sleep(programConfig.success_seconds)
            if pipe.poll() is None:
                success = True
                break
            else:
                restartDelay = programConfig.restartdelay - programConfig.success_seconds
                if restartDelay > 0:
                    time.sleep(restartDelay)

        if success is False:
            return False

        self.pid = int(pipe.pid)
        self.setCmdlineFromProc()
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
                while now < maxTimeBeforeKill:
                    # If process has died, abort.
                    if not os.path.exists('/proc/%d' %(self.pid,)):
                        break
                    # Otherwise, wait 100ms before checking again.
                    time.sleep(.1)
                    now = time.time()

                # If program has not terminated given the threshold, send 'er the ol' boot.
                if now >= maxTimeBeforeKill:
                    os.kill(self.pid, signal.SIGKILL)
            except:
                pass

        # Remove pid file
        self.removePidFile(programConfig)
