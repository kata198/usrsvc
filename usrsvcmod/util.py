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


    usrsvc is a user process manager
'''

# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :

import os
import socket
import pwd
import time

__all__ =  ('waitUpTo', 'getUsername', 'getHostname', 'findProgramPath' )


def waitUpTo(testFunc, funcArgs, timeout, interval=0.1):
    '''
        waitUpTo - Wait up to a certain amount of time, or until a provided test function
            returns False.

        @param testFunc <function/lambda> - Test function, True if keep going else False
        @param funcArgs <list/tuple> - Args to past to test function
        @param timeout <float> - Max number  of seconds to wait
        @param interval <float> - Interval between polls. Does not make sense to be > timeout.

        @return - True if timeout occured (function never returned False), otherwise False.
    '''
    if not isinstance(funcArgs, tuple):
        funcArgs = tuple(funcArgs)

    maxTime = time.time() + timeout
    keepGoing = funcResult = testFunc(*funcArgs)

    while keepGoing is True:
        time.sleep(interval)
        now = time.time()
        funcResult = testFunc(*funcArgs)
        keepGoing = (now < maxTime and funcResult is True)

    return not funcResult

def getUsername():
    try:
        return pwd.getpwuid(os.getuid()).pw_nam
    except:
        try:
            return os.environ['USER']
        except:
            pass

    return 'unknown'

def getHostname():
    # Try fqdn first, if localhost, get short name.
    hostname = socket.getfqdn()
    if 'localhost' in hostname:
        hostname = socket.gethostname()
    return hostname

def findProgramPath(programName, environPath=None):
    '''
        findProgramPath - Find the path to an excutable.

        @param programName - Name to searh
        @param env - PATH to search, or None to use os.environ['PATH']

        @return - Path to program if found, otherwise None
    '''
    if environPath is None:
        environPath = os.environ['PATH']

    for path in environPath.split(':'):
        if not path:
            continue
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        tryPath = path + '/' + programName
        if os.access(tryPath, os.X_OK):
            return tryPath

    return None

def camelToWords(camelStr):
    '''
        camelToWords - Converts a camel-case item into words, by appending a space before every capital letter at index i>0

        Example: ActivityFileMonitor returns "Activity File Monitor"

        @param camelStr <str> - A string to convert

        @return <str> - Words transformed from camel case string
    '''
    if len(camelStr) == 0:
        return ''

    ret = []
    camelStrSplit = list(camelStr)

    # If first char is lowercase, uppercase it.
    ret.append(camelStrSplit[0].upper())

    for x in camelStrSplit[1:]:
        if x.isupper():
            ret.append(' ')
        ret.append(x)

    return ''.join(ret)


# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :
