usrsvc
======

A service manager for running/managing/monitoring/auto-restarting daemons and services at the user (non-root) level

Intended for managing services/daemons running as service account users.


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



**Verbose**

Usrsvc and usrsvcd are very verbose with logging, and try to be as specific as possible. All logs contain timestamps and meaningful error codes/descriptions, to simplify and even make possible evaluation of issues with your services.



**Email Alerts**

When the "email_alerts" property is set on a Program or a Program Group, an email will be sent when Monitoring triggers a restart, or the program is found to not be running and is started by usrsvcd.



Process Identification
----------------------

The primary method for managing processes are through pidfiles. Every program is required to have a pidfile defined in its configuration.


When autopid = True (default), usrsvc will manage the pidfile. If you set autopid = False, your application will need to generate its own pidfile (not recommended).

The process identified by the pid file will be checked against *proctitle_re*, and if they don't match, the pid file will be considered stale and removed.


**Starting Processes**

When usrsvc starts a process, it will run for *success_seconds*, in which time it will try to match a process (based on *proctitle_re*), and ensure that process is still running at the end of that period.


When useshell = True, usrsvc will fork and exec a bash process (provided as *command*) which should launch your process, or when useshell = False, it will launch the given *command* directly.

That process, and its children, and all of their children, etc, will be checked against *proctitle_re* for a match.

If your process takes a long time to start, you will likely need to increase *success_seconds* from its default value.

When the process is matched, and the period ends, usrsvc will write the pidfile (autopid = True) and return success, otherwise it will return failure.


**Scanning for Processes**

When *scan_for_process* is True (default), in the absense of a pid file, or when a pid file is declared stale (does not match *proctitle_re*),
 usrsvc will scan all processes running as the current user for one that matches *proctitle_re*.


If a match is found, it will update the pidfile with the matched program.

If at all possible, you should ensure that you have unique proctitles for your applications, such that you can safely have *scan_for_process* = True. 

This provides a fallback in the case that a service is started via some other means, or the pid file is removed or otherwise corrupted.

In addition to working as a fallback, this allows you to attach usrsvc to any existing running service, *without the need to restart that service*.
You can attach and detach usrsvc to any process at-will.

After a process is found via scan, its pid will be written to the pidfile, which is the primary (and most efficient) means of associating a process to a name.


Many services have the means to set the proctitle to something unique, via setproctitle system call, python library "setproctitle", etc.

It is recommended whenever possible to have *scan_for_process* be True, to add the extra resiliency and managibility.



usrsvc (tool)
-------------


The "usrsvc" tool handles the basic operations of starting/stopping/restarting/status of a service. You can use this with or without *usrsvcd* running to manage services.


	Usage: usrsvc (Options) [start/stop/restart/status] [program name]

		Performs the requested action on the given program name.

		"all" can be used in place of "program name" to perform the given task on all configured programs. (see Parallel below)

	 
	usrsvc is the tool for performing specific actions on services, usrsvcd is the related daemon for autorestart/monitoring, etc.


	Options:

	\-\-\-\-\-\-\-\-


		Parallel:

			When doing start/stop/restart all, you may add "\-\-parallel" or "\-P" to perform 

			the action on all items in parallel.

			  

	Config:

	\-\-\-\-\-\-\-


		Usrsvc uses the config file found at $HOME/usrsvc.cfg (/home/media/usrsvc.cfg).


	Documentation

	\-\-\-\-\-\-\-\-\-\-\-\-\-


		Run "usrsvc \-\-readme" or see https://github.com/kata198/usrsvc/blob/master/README.md 

		  for more documentation.


The tool will output some basic information about what happened, and give a meaningful return code (0 = success, otherwise see https://raw.githubusercontent.com/kata198/usrsvc/master/usrsvcmod/constants.py "ReturnCodes" object for the list of return codes used and descriptions).

Usrsvc will be as verbose as possible in identifying why a program failed to start and stay running, to ease debugging.


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

The *usrsvcd* daemon handles the autostart, autorestart, and monitoring of the configured services. It is optional, but required for advanced features.


	Usage: usrsvcd (Optional: [action])


	Usrsvcd is the daemon portion of usrsvc which actively monitors processes,

	  provides autostart, autorestart, and other advanced features.


	If "action" is omitted, it will assume the default, "start".


		Actions:


			checkconfig            -   Try to parse config files and validate correctness, without affecting the running usrsvcd instance. Returns non-zero on failure.

			reread                 -   Sends SIGUSR1 to the running usrsvcd process, which will cause it to reread configs and immediately apply the changes to the running instance.

										If there are errors in the configs, a message will be logged by the usrsvcd process and it will retain its current configuration state.

			restart                -   Restarts the usrsvcd daemon cleanly

			status                 -   Checks if usrsvcd is running. Returns non-zero on failure

			stop                   -   Stops running instance of usrsvcd


	Uses main config file in $HOME/usrsvc.cfg


The *usrsvcd* process will pick up the state of any configured services (whether they are running, what their pid is, etc) when it starts. Unlike other managers, it does not need to restart the program to begin managing it.



**Updating Configuration**

With usrsvcd, you can add or remove a service, or change the properties of an existing service, without disruption of any of the applications.


Simply make the changes to the configuration, and run *usrsvcd checkconfig* to validate against any configuration errors. If there are errors, you will be alerted to what they are, and *usrsvcd* will continue to operate off the last good configuration.

When you are satisfied and have validated your changes, run *usrsvcd reread* to tell usrsvcd to update its internal copy of your configuration. Usrsvcd will perform a check prior to loading the new config, and will alert you if there is an error (and retain the last good config).


After your changes have been validated, usrsvcd will apply the updates following the completion of its current operation set. This makes it safe to update at any time, without worry of disruption to applications.

There is no need to restart usrsvcd to apply a configuration change.



Configuration
=============


Configuration starts with the "main" config at $HOME/usrsvc.cfg . This file defines some basic info, or can contain your full configuration if you want. The recommended usage is to provide the "config_dir" property therein, which specifies a directory. In that directory, all files ending in ".cfg" will be processed, allowing you to have each Program defined in its own config, default settings in another config, etc. This makes it simpler to manage and add/remove services.


Configuration is "configobj" style, which closely mimics ini-style but supports subsections.

The following are the sections and their meanings. [Main] must be defined in $HOME/usrsvc.cfg, but otherwise any of the sections can appear in any config file.


Main Config
-----------

**[Main]**

The [Main] section must be found in $HOME/usrsvc.cfg, and can contain any of the following properties:


* config_dir - This defines a directory which will be searched for additional configuration. Anything with a ".cfg" suffix will be processed as a config.

* pidfile - REQUIRED - This defines the location where *usrsvcd* will store its own pid.

* usrsvcd_stdout - If defined, usrsvcd will log stdout to this file instead of the default stdout (likely a terminal). Must be an absolute path.

* usrsvcd_stderr - If defined, usrsvcd will log stderr to this file instead of the default stderr (likely a terminal). Use the value "stdout" to log stderr to the same location as stdout, otherwise must be an absolute path.

* sendmail_path - If defined and not "auto", this should be the path to the "sendmail" application. This is used as the sender program when "email_alerts" is set on a Program. If not defined or auto, /usr/sbin/sendmail, /usr/bin/sendmail, and every element in PATH will be checked.


Program Config
--------------


**[Program:myprogram]**

Each "Program" section can be in any config file, and defines a Program that will be managed by usrsvc. Following the colon is the program name (in this case, "myprogram") and must be unique. This will assign the name that will be used to identify the program (e.x. "usrsvc start myprogram")


The "Program" section has the following properties:


* command - REQUIRED - Full command and arguments to execute. If #useshell# is True, this can contain shell-isms

* useshell - Boolean, default False. If True, will invoke your application through a shell. You can use shell expressions in this mode. Use "False" if you don't need this.

* pidfile - REQUIRED - Path to a pidfile. If #autopid# is False, your app must write its pid to this file. Otherwise, usrsvcd will mangage it, even with #scan_for_process# or other methods.

* enabled - Boolean, default True. Set to "False" to disable the program from being managed by "usrsvcd"

* autopid - Default True, boolean. If True, "usrsvc" and "usrsvcd" will write the pid of the launched program to the pidfile, i.e. managed. If your application forks-and-exits, you can set this to FAlse and write your own pid, or use #scan_for_process#

* scan_for_process - Default True, boolean. If True, "usrsvc" and "usrsvcd" will, in the absense of a pidfile which matches with #proctitle_re#, use #proctitle_re# and scan running processes for the application. This can find applications even when the pidfile has gone missing.

* proctitle_re - None or a regular expression which will match the proctitle (can be seen as last col in "ps auxww").  If none provided, a default wherein the command and arguments are used, will work in almost all instances. Some applications modify their proctitle, and you may need to use this to match them.



* autostart - Default True, boolean value if program should be started if not already running when "usrsvcd" is invoked

* autorestart - Default True, boolean value if program should be restarted if it stopped while "usrsvcd" is running

* maxrestarts - Default 0, integer on the max number of times usrsvcd will try to automatically restart the application by "usrsvcd". If it is seen running again naturally, this counter will reset. 0 means unlimited restarts.

* restart_delay - Default 0, integer on the miminum number of seconds between a failing "start" and the next "restart" attmept by "usrsvcd". 

* success_seconds - Default 2, Float, The number of seconds usrsvc will wait before considering a program successfully started. The created process must both match and still be running at the end of this period to be marked successful.

* term_to_kill_seconds : Default 8, Float on the number of seconds the application is given between SIGTERM and SIGKILL.



NOTE: The following stdout/stderr are opened in "append" mode always. 

* stdout - REQUIRED - Absolute path to a file to be used for stdout

* stderr - Absolute path to a file to be used for stderr, or "stdout" to redirect to stdout. Default is to redirect stderr to stdout. May be same filename as stdout.

* defaults - This can reference a "DefaultSettings" section defined elsewhere, i.e. to reference [DefaultSettings:MySettings] use "defaults=MySettings". If provided, this Program will inherit the settings defined in the DefaultSettings as the defaults. Anything provided explicitly in this Program will override those found in the defaults.

* inherit_env - Boolean, default True. If True, will inherit the env from "usrsvc" or "usrsvcd". Otherwise, will only use the Env as defined in the Env subsection.

* email_alerts - String, if set, when usrsvcd starts/restarts a process, an email alert will go to this address.


Program Subsections
-------------------

Your *Program* config may contain the following subsections, and their properties.


**[[Env]]**

A series of key=value items which will be present in the environment prior to starting this Program.



**[[Monitor]]**

The Monitor subsection specifies if and how your *Program* will be monitored. Monitoring can determine if a *Program* has stopped running, or exceeded some bounds, and trigger a restart.

Currently, *Monitor* can contain the following properties:

* monitor_after - Minimum number of seconds that program needs to be running before monitoring will begin. Default 30. 0 disables this feature.

(Activity File Monitoring)

The following two properties deal with "activity file" monitoring, that is ensuring that a file or directory is updated within a specified number of seconds.

* activityfile - File or Directory which must be modified every #activityfile_limit# seconds, or program will be restarted. Default undefined/empty string disables this.

* activityfile_limit - If activityfile is defined, this is the number of seconds is the maximum that can go between modifications of the provided #activityfile# before triggering a restart.

(RSS Limit Monitoring)

The following property triggers the "rss limit" monitor. This monitor checks the Resident Set Size (non-shared memory an application is using), and restarts if it exceeds a given threshold.

* rss_limit - Default 0, if greater than zero, specifies the maximum RSS (resident set size) that a process may use before being restarted. This is the "private" memory (not including shared maps, etc) used by a process.


*Example Program Config:* 


	[Program:myprogram]


	command = /home/myusr/bin/myprogram.py arg1 arg2

	pidfile = /home/myusr/pids/myprogram.pid

	stdout  = /home/myusr/logs/myprogram.log

	stderr  = stdout


	[[Env]]


		DB_USER = superdb

		DB_NAME = mydatabase



Inheritable Settings
--------------------

You can define default settings in a .cfg file within your *config_dir* that can be inherited by other programs. Use this to reduce duplication, and change things en masse.
 
Set the *defaults* property of a Program to the name given to a *DefaultsSettings* section to have that Program inherit those defaults.

Any properties defined by the Program explicitly will override any defaults inherited.


*Example DefaultSetings*


	[DefaultSettings:mydefaults]

				success_seconds = 5

				restart_delay = 3

				max_restarts = 3

				email_alerts = nobody@example.com


Systemd Integration
-------------------

As of 1.5.9 usrsvcd is integrated with systemd. In the source distribution, you'll find a "systemd" directory which contains a unit, and an install.sh script to install it.

If usrsvcd is installed somewhere other than "/usr/bin/usrsvcd", you'll need to modify the lines in "usrsvcd@.service" that start with "Exec" with the correct path.


Use "systemctl start usrsvcd@myuser" to start usrsvcd as "myuser"

Use "systemctl enable usrsvcd@myuser" to enable usrsvcd to start as "myuser" on boot.

As per the design of usrsvc, you can have multiple daemons enabled for multiple users.


Examples
--------

An example configuration can be found in the "examples" directory ( https://github.com/kata198/usrsvc/tree/master/examples ). The "usrsvc.cfg" is the main configuration file (to be located in $HOME/usrsvc.cfg), and the "cfg" directory is intended to be "/home/myusr/usrsvc.d/cfg" (per config_dir value in usrsvc.cfg



Contact Me
----------

You may reach me for support, questions, feature requests, or just to let me know you're using it! Use the email kata198 at gmail.



Changes
-------

The Changelog can be found at: https://raw.githubusercontent.com/kata198/usrsvc/master/ChangeLog
