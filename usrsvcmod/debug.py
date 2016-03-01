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


    debug - Controls some extra diagnostic debugging stuff
'''

__all__ = ('isDebugEnabled', 'toggleDebug')

global _USRSVCMOD_DEBUG
_USRSVCMOD_DEBUG = False

def isDebugEnabled():
    global _USRSVCMOD_DEBUG
    return _USRSVCMOD_DEBUG

def toggleDebug(isEnabled):
    global _USRSVCMOD_DEBUG
    _USRSVCMOD_DEBUG = bool(isEnabled)
