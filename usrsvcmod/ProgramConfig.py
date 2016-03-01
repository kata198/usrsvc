'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv3, with additions/modifications.
    This may change at my discretion, retroactively, and without notice.

    You should have received a copy of this with the source distribution as a file titled, LICENSE,
    and additions in a file titled LICENSE.additions. 

    In any situation that LICENSE.additions 

    The most current license can be found at:
    https://github.com/kata198/usrsvc/LICENSE

    and additions/modifications at:
    https://github.com/kata198/usrsvc/LICENSE.additions

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

    def __init__(self, name, 
            command=None, pidfile=None, autostart=True,
            autorestart=True, maxrestarts=0, restart_delay=0,
            autopid=True, useshell=True, proctitle_re=None, 
            success_seconds=2, term_to_kill_seconds=3, scan_for_process=False,
            stdout=None, stderr=None,
            enabled=True,
            inherit_env=True, Env=None, Monitoring=None,
            defaults=None,
            **kwargs):
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
        #   Do not use start or end because given a shebang line, the executable may change.
        if not proctitle_re:
            proctitle_re = re.compile('(%s)' %(re.escape(' '.join(commandSplit)), ))

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
            raise ValueError('Unknown config options: %s' %(str(kwargs.keys()), ))

    def __str__(self):
        return str(self.__dict__)
