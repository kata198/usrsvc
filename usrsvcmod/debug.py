'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

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
