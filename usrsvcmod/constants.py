
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

    # Specific meanings
    INVALID_CONFIG  = 130
    INVALID_ACTION  = 131
    PROGRAM_DISABLED = 132
    PROGRAM_UNDEFINED = 133
    PROGRAM_FAILED_TO_START = 134
    USRSVCD_ALREADY_RUNNING = 135
    INSUFFICIENT_PERMISSIONS = 136
    
    # Unknown exception occured, state of program is unknown.
    UNKNOWN_FAILURE = 254
