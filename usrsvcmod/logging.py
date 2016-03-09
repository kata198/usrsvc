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


    logging - some general logging functions
'''

import datetime
import sys

__all__ = ('logMsg', 'logErr')

# TODO: Notification system

def _getCtime():
    return datetime.datetime.now().ctime()


def logMsg(msg, includeDate=True):
    '''
        logMsg - log a message (stdout)
    '''
    if includeDate is True:
        sys.stdout.write("[%s] - %s" %(_getCtime(), msg))
    sys.stdout.flush()

def logErr(msg, includeDate=True):
    '''
        logErr - log an error (stderr)
    '''
    if includeDate is True:
        sys.stderr.write("[%s] - %s" %(_getCtime(), msg))
    sys.stderr.flush()
