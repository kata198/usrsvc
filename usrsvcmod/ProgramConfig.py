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


    'ProgramConfig' represents a single program config
'''

import os
import re
import shlex

from .configcommon import getConfigValueBool, getConfigValueInt, getConfigValueFloat
from .MonitoringConfig import MonitoringConfig

__all__ = ('ProgramConfig', )

class ProgramConfig(object):
    '''
        ProgramConfig - The configuration for a Program. [Program:TheName] would be named "TheName"
    '''

    def __init__(self, name, 
            command=None, pidfile=None, autostart=True,
            autorestart=True, maxrestarts=0, restart_delay=0,
            autopid=True, useshell=True, proctitle_re=None, 
            success_seconds=2.0, term_to_kill_seconds=8.0, scan_for_process=True,
            stdout=None, stderr=None,
            enabled=True,
            inherit_env=True, Env=None, Monitoring=None,
            defaults=None,
            **kwargs):
        '''
            name - Determined from section name [Program:TheName] has "TheName"

            Params:

                * command - REQUIRED - Full command and arguments to execute. If #useshell# is True, this can contain shell-isms
                * useshell - If True, will invoke your application through a shell. You can use shell expressions in this mode. Use "False" if you don't need this.
                * pidfile - REQUIRED - Path to a pidfile. If #autopid# is False, your app must write its pid to this file. Otherwise, usrsvcd will mangage it, even with #scan_for_process# or other methods.
                * enabled - Boolean, default True. Set to "False" to disable the program from being managed by "usrsvcd"
                * autopid - Default True, boolean. If True, "usrsvc" and "usrsvcd" will write the pid of the launched program to the pidfile, i.e. managed. If your application forks-and-exits, you can set this to FAlse and write your own pid, or use #scan_for_process#
                * scan_for_process - Default True, boolean. If True, "usrsvc" and "usrsvcd" will, in the absense of a pidfile which matches with #proctitle_re#, use #proctitle_re# and scan running processes for the application. This can find applications even when the pidfile has gone missing.
                * proctitle_re - None or a regular expression which will match the proctitle (can be seen as last col in "ps auxww").  If none provided, a default wherein the command and arguments are used, will work in almost all instances. Some applications modify their proctitle, and you may need to use this to match them.

            
                * autostart - Default True, boolean value if program should be started if not already running when "usrsvcd" is invoked
                * autorestart - Default True, boolean value if program should be restarted if it stopped while "usrsvcd" is running
                * maxrestarts - Default 0, integer on the max number of times usrsvcd will try to automatically restart the application by "usrsvcd". If it is seen running again naturally, this counter will reset. 0 means unlimited restarts.
                * restart_delay - Default 0, integer on the miminum number of seconds between a failing "start" and the next "restart" attmept by "usrsvcd". 
                * success_seconds - Default 2, Float on the number of seconds the application must be running for "usrsvc" to consider it successfully started.
                * term_to_kill_seconds : Default 8, Float on the number of seconds the application is given between SIGTERM and SIGKILL.



                NOTE: The following stdout/stderr are opened in "append" mode always. 
                * stdout - REQUIRED - Absolute path to a file to be used for stdout
                * stderr - Absolute path to a file to be used for stderr, or "stdout" to redirect to stdout. Default is to redirect stderr to stdout. May be same filename as stdout.
                * defaults - This can reference a "DefaultSettings" section defined elsewhere, i.e. to reference [DefaultSettings:MySettings] use "defaults=MySettings". If provided, this Program will inherit the settings defined in the DefaultSettings as the defaults. Anything provided explicitly in this Program will override those found in the defaults.
                * inherit_env - Boolean, default True. If True, will inherit the env from "usrsvc" or "usrsvcd". Otherwise, will only use the Env as defined in the Env subsection.

                Supports the following subsections:

                [[Monitor]]
                  - See MonitoringConfig

                [[Env]]
                  key=value

                pairs for environment variables. Affected by #inherit_env above.
        '''


        self.command = command
        self.pidfile = pidfile
        if not pidfile or pidfile[0] != '/':
            raise ValueError('pidfile must be defined for a program and must be an absolute path.')
        self.enabled = getConfigValueBool(enabled, 'enabled')
        self.autostart = getConfigValueBool(autostart, 'autostart')
        self.autorestart = getConfigValueBool(autorestart, 'autorestart')
        self.maxrestarts = getConfigValueInt(maxrestarts, 'maxrestarts')
        self.restart_delay = getConfigValueInt(restart_delay, 'restart_delay')
        self.success_seconds = getConfigValueFloat(success_seconds, 'success_seconds')
        self.autopid = getConfigValueBool(autopid, 'autopid')
        self.useshell = getConfigValueBool(useshell, 'useshell')
        self.scan_for_process = getConfigValueBool(scan_for_process, 'scan_for_process')
        self.term_to_kill_seconds = getConfigValueFloat(term_to_kill_seconds, 'term_to_kill_seconds')

        if self.term_to_kill_seconds < 0:
            raise ValueError('term_to_kill_seconds is required and must be a positive number.')

        self.inherit_env = getConfigValueBool(inherit_env, 'inherit_env')
        self.defaults = defaults
        
        if not issubclass(Env.__class__, (type(None), dict)):
            raise ValueError('Env must be a subsection, like [[Env]]')

        if Env is None:
            Env = {}
        self.Env = Env

        if not issubclass(Monitoring.__class__, (type(None), dict)):
            raise ValueError('Monitoring must be a subsection, like [[Monitoring]]')
        if Monitoring is None:
            Monitoring = {}
        self.Monitoring = MonitoringConfig(**Monitoring)


        if not name:
            raise ValueError('Program Config defined without a name.')
        self.name = name

        if not command:
            raise ValueError('Missing command for program: "%s"' %(name,))

        try:
            commandSplit = shlex.split(command)
        except ValueError as e:
            raise ValueError('Cannot parse command,\n%s\nError: %s' %(command, str(e)))

        # If proctitle_re is not defined, default to the provided command.
        #   Do not use start because given a shebang line, the executable may change.
        if not proctitle_re:
            proctitle_re = re.compile('(%s)$' %(re.escape(' '.join(commandSplit)), ))

        self.proctitle_re = proctitle_re
            
        if not stdout:
            raise ValueError('Program %s does not define a value for stdout.' %(name,))
        elif stdout[0] != '/':
            raise ValueError('Program %s has invalid stdout path "%s", must be absolute.' %(name, stdout))

        if not os.path.isdir(os.path.dirname(stdout)):
            raise ValueError('Program %s defines a stdout path as "%s" but the folder %s does not exist.' %(name, stdout, os.path.dirname(stdout)))

        self.stdout = stdout

        if not stderr or stderr == 'stdout':
            self.stderr = stdout
        else:
            if stderr[0] != '/':
                raise ValueError('Program %s has invalid stderr path "%s", must be absolute.' %(name, stderr))
            if not os.path.isdir(os.path.dirname(stderr)):
                raise ValueError('Program %s defines a stderr path as "%s" but the folder %s does not exist.' %(name, stderr, os.path.dirname(stderr)))

            self.stderr = stderr

        if kwargs:
            raise ValueError('Unknown config options: %s' %(str(list(kwargs.keys())), ))

    def __str__(self):
        return str(self.__dict__)
