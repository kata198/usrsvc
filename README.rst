usrsvc
======

A user service manager. Intended for managing services/daemons running as service account users.



Design
------

usrsvc comes in two parts, *usrsvc* (tool to start/stop/restart/get status of services) and *usrsvcd* (daemon which keeps services running, monitors running services, etc). 

You may use *usrsvc* standalone, or in conjunction with *usrsvcd*.


**No Parent/Child**

Contrary to other service managers, such as supervisord, usrsvcd does NOT require itself be the parent of the processes it manages. This allows usrsvcd to be restarted, updated, or not run at all, without affecting the services it manages.

In the supervisord world, if you need to update the running supervisord, you must also restart all processes that it is managing which causes an unnecessary outage.

All services started by *usrsvc* or *usrsvcd* have "init" as the parent (or systemd under some system configurations).


**Capturing/Managing existing processes**

Because no parent-child relationship is required or even used, usrsvc is able to manage already-running processes. There are several configurable means for usrsvc to identify and match the services you define to running processes.


**Modular / Resilient**


Instead of one monolithic daemon, usrsvc is broken into *usrsvc* (tool to start/stop/restart/status), daemon *usrsvcd* (tool to manage autostart, autorestart, monitoring), and in the future an XLMRPC daemon for a web interface.

Each tool does exactly just what it needs to do, and is designed to recover from any failure scenario and keep going. 

You can, for example, run "usrsvcd reread" (or send USR1 signal to usrsvcd process) to have it attempt to reread the configuration. If there is an error with the new configuration, it will be logged, and the old configuration retained. 
If the new configuration passes validation, the changes will be applied to the next set of operations performed by usrsvcd. Unlike other service managers, *usrsvcd* will not crash with a configuration error.


Several commands / log entries give a JSON output so they can be parsed and used by an external application.


**Process Monitoring**


*usrsvcd* provides the ability to monitor the processes it manages beyond just whether it is stopped/started. These are configurable, optional, and defined per-service (see "Monitoring" section below.)


**No root / Isolation**

usrsvc is designed to run at the service account level, per best-practices of security isolation. It requires no root configuration or service to be running; everything is isolated to the user account running the service (like "web" or "django")

Each account has its own independent configurations, and runs its own instance of *usrsvcd*, providing further isolation between application groups.


**Simple Configuration**

All of the configuration is through simple ini-style config files, and supports defining and inheriting default settings to prevent duplication across programs.


usrsvc (tool)
-------------


The "usrsvc" tool handles the basic operations of starting/stopping/restarting/status of a service. You can use this with or without *usrsvcd* running to manage services.


	Usage: usrsvc [start/stop/restart/status] [program name]

	  Performs the requested action on the given program name.

	 "all" can be used for start/stop/restart.


	Uses the config file found at $HOME/usrsvc.cfg


The tool will output some basic information about what happened, and give a meaningful return code (0 = success, otherwise see https://raw.githubusercontent.com/kata198/usrsvc/master/usrsvcmod/constants.py "ReturnCodes" object for the list of return codes used)

**Example Usage**

start:

	[myuser]$ usrsvc start MagicLooper

	[Tue Mar  8 22:14:34 2016] - Started MagicLooper:


	{'args': ['/home/svcact/bin/MagicLooper.py'], 'cmdline': '/usr/bin/python /home/svcact/bin/MagicLooper.py', 'pid': 12467, 'executable': '/usr/bin/python', 'running': True}



status:

	[myuser]$ usrsvc status MagicLooper

	[Tue Mar  8 22:14:55 2016] - MagicLooper is running:


	{'args': ['/home/svcact/bin/MagicLooper.py'], 'cmdline': '/usr/bin/python /home/svcact/bin/MagicLooper.py', 'pid': 12467, 'executable': '/usr/bin/python', 'running': True}


stop:

	[myuser]$ usrsvc stop MagicLooper

	[Tue Mar  8 22:15:37 2016] - Stopping MagicLooper [12467]

	[Tue Mar  8 22:15:37 2016] - MagicLooper terminated


usrsvcd (daemon)
----------------

The *usrsvcd* daemon handles the autostart, autorestart, and monitoring of the configured services. It is optional, and not required to use usrsvc, but required for advanced features.

	Usage: usrsvcd (Optional: [action])

	Optional daemon portion of usrsvc which actively monitors processes and provides the autostart/autorestart, and other optional features.


		Actions:

			Running with no arguments starts the usrsvcd daemon. You can also provide one of several "action" arguments which affect the running instance of usrsvcd.


			checkconfig            -   Try to parse config files and validate correctness, without affecting the running usrsvcd instance. Returns non-zero on failure.

			reread                 -   Sends SIGUSR1 to the running usrsvcd process, which will cause it to reread configs and immediately apply the changes to the running instance.

										If there are errors in the configs, a message will be logged by the usrsvcd process and it will retain its current configuration state.

			restart                -   Restarts the usrsvcd daemon cleanly

			status                 -   Checks if usrsvcd is running. Returns non-zero on failure


	Uses main config file in $HOME/usrsvc.cfg



The *usrsvcd* process when started will pick up the state of any configured services (whether they are running, what their pid is, etc), it does not need to start/restart the processes to manage them.

**Reread config live**

If you want to add/remove/change a service or a service's properties, you can do so by updating the configuration files, and then optionally running "usrsvcd checkconfig" (to validate config and give you errors on stderr), followed by "usrsvcd reread".

If there are errors in the configs, they will be logged and the previous configuration will be kept. Otherwise, after the current operation set is completed, *usrsvcd* will update all its internal references to the new config, and continue with them.

There is no need to restart usrsvcd or any of its services to apply a config change in this regard.




Configuration
=============


Configuration starts with the "main" config at $HOME/usrsvc.cfg . This file defines some basic info, or can contain your full configuration if you want. The recommended usage is to provide the "config_dir" property therein, which specifies a directory. In that directory, all files ending in ".cfg" will be processed, allowing you to have each Program defined in its own config, default settings in another config, etc. This makes it simpler to manage and add/remove services.


Configuration is "configobj" style, which closely mimics ini-style but supports subsections.

The following are the sections and their meanings. [Main] must be defined in $HOME/usrsvc.cfg, but otherwise any of the sections can appear in any config file.


**[Main]**

The [Main] section must be found in $HOME/usrsvc.cfg, and can contain any of the following properties:


* config_dir - This defines a directory which will be searched for additional configuration. Anything with a ".cfg" suffix will be processed as a config.

* pidfile - REQUIRED - This defines the location where *usrsvcd* will store its own pid.

* usrsvcd_stdout - If defined, usrsvcd will log stdout to this file instead of the default stdout (likely a terminal). Must be an absolute path.

* usrsvcd_stderr - If defined, usrsvcd will log stderr to this file instead of the default stderr (likely a terminal). Use the value "stdout" to log stderr to the same location as stdout, otherwise must be an absolute path.


**[Program:myprogram]**

Each "Program" section can be in any config file, and defines a Program that will be managed by usrsvc. Following the colon is the program name (in this case, "myprogram") and must be unique. This will assign the name that will be used to identify the program (e.x. "usrsvc start myprogram")


The "Program" section has the following properties:


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



"Program" Supports the following subsections:

[[Monitor]]

The monitoring section, see below for more info.

[[Env]]

A series of key=value items which will be present in the environment prior to starting this Program.


*Example Program Config:* 


	[Program:myprogram]


	command = /home/myusr/bin/myprogram

	pidfile = /home/myusr/pids/myprogram.pid

	stdout  = /home/myusr/logs/myprogram.log

	stderr  = stdout


	[[Env]]


		DB_USER = superdb

		DB_NAME = mydatabase



**[DefaultSettings:mydefaults]**

These define a set of default settings for a Program, and can include default values in subsections as well. Your program can inherit these default settings by setting the "defaults=mydefaults" property, where "mydefaults" is the name of your DefaultSettings.


**[[Monitor]]**

The Monitor subsection specifies if and how your Program will be monitored. This is to sense if your Program has frozen and needs a restart, the "autorestart" and "autostart" monitoring are handled in the "Program" config.

Note, additional Monitoring types will be available in a future release.

Monitor can contain the following properties:

* monitor_after - Minimum number of seconds that program needs to be running before monitoring will begin. Default 30. 0 disables this feature.

* activityfile - File or Directory which must be modified every #activityfile_limit# seconds, or program will be restarted. Default undefined/empty string disables this.

* activityfile_limit - If activityfile is defined, this is the number of seconds is the maximum that can go between modifications of the provided #activityfile# before triggering a restart.


