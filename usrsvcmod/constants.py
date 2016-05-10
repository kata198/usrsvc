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


    constants for usrsvc
'''

try:
    from enum import IntEnum
except ImportError:
    # We only support 2.7+ anyway, but some older 2.7s don't have the enum type.
    IntEnum = object

class ReturnCodes(IntEnum):
    
    # A general success
    SUCCESS = 0

    # A general failure
    GENERAL_FAILURE = 1

    TRY_AGAIN = 11  # Same as EAGAIN on Linux. Should try operation again.

    #### Specific meanings ###

    # Config does not parse or is otherwise invalid
    INVALID_CONFIG  = 130

    # An action was requested that does not exist
    INVALID_ACTION  = 131

    # The program was disabled
    PROGRAM_DISABLED = 132

    # The program requested is not defined in configs
    PROGRAM_UNDEFINED = 133

    # Program was launched, but died before #success_seconds# passed.
    PROGRAM_EXITED_UNEXPECTEDLY = 134

    # Usrsvcd was started but another instance is already running as current user
    USRSVCD_ALREADY_RUNNING = 135

    # Insufficient permissions to perform the action (usually file permissions)
    INSUFFICIENT_PERMISSIONS = 136

    # Called when an invalid command or if cannot execute given command
    PROGRAM_FAILED_TO_LAUNCH = 137

    # Returned when a help option (like  --help or  --readme) is used
    HELP_MESSAGE = 138
    
    # Unknown exception occured, state of program is unknown.
    UNKNOWN_FAILURE = 254

    if IntEnum != object:
        # Preferred method using enum
        @classmethod
        def returnCodeToString(cls, returnCodeValue):
            try:
                returnCodeValue = int(returnCodeValue)
            except ValueError:
                # Should be an exception, but let's go for the more durable route.
                return 'INVALID_RETURN(%s)' %(str(returnCodeValue),)
                #raise ValueError('returnCodeToString called with non-integer value: %s' %(str(returnCodeValue),))

            for item in cls:
                if item.value == returnCodeValue:
                    return item.name

            return 'UNKNOWN(%d)' %(returnCodeValue,)
    else:
        # Backup method for older pythons without enum
        @classmethod
        def returnCodeToString(cls, returnCodeValue):
            try:
                returnCodeValue = int(returnCodeValue)
            except ValueError:
                return 'INVALID_RETURN(%s)' %(str(returnCodeValue),)

            for attrName in dir(cls):
                attrValue = getattr(cls, attrName)
                if not isinstance(attrValue, int):
                    continue
                if attrValue == returnCodeValue:
                    return attrName

            return 'UNKNOWN(%d)' %(returnCodeValue,)

