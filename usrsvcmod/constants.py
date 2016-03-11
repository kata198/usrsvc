
try:
    from enum import IntEnum
except ImportError:
    # We only support 2.7+ anyway, but fallback for some reason.
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
    
    # Unknown exception occured, state of program is unknown.
    UNKNOWN_FAILURE = 254

    @classmethod
    def returnCodeToString(cls, returnCodeValue):
        try:
            returnCodeValue = int(returnCodeValue)
        except ValueError:
            return 'INVALID_RETURN(%s)' %(str(returnCodeValue),)
#            raise ValueError('returnCodeToString called with non-integer value: %s' %(str(returnCodeValue),))
            # Should be an exception, but let's go for the more durable route.

        for item in cls:
            if item.value == returnCodeValue:
                return item.name

        return 'UNKNOWN(%d)' %(returnCodeValue,)

