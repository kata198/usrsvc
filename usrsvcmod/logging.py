'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    logging - some general logging functions
'''

import datetime
import sys

__all__ = ('logMsg', 'logErr')

# TODO: Notification system

def _getCtime():
    return datetime.datetime.now().ctime()


def logMsg(msg, includeDate=True):
    if includeDate is True:
        sys.stdout.write("[%s] - %s" %(_getCtime(), msg))
    sys.stdout.flush()

def logErr(msg, includeDate=True):
    if includeDate is True:
        sys.stderr.write("[%s] - %s" %(_getCtime(), msg))
    sys.stderr.flush()
