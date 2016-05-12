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

import time

__all__ =  ('waitUpTo', )


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

