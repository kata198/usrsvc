'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    usrsvc is a user process manager
'''
import re

__all__ = ('getConfigValueBool', 'getConfigValueInt', 'getConfigValueFloat')

def getConfigValueBool(value, name=''):
    if type(value) == bool:
        return value
    else:
        value = str(value)
        if value.isdigit():
            return bool(int(value))
        value = value.lower()
        if value == 'true':
            return True
        if value == 'false':
            return False

    if name:
        errPart = ' for config parameter %s' %(name,)
    else:
        errPart = ''

    raise ValueError('Unknown value%s: %s. Should be True/1 or False/0' %(errPart, value) )

# Keep in mind that getConfigValueInt and getConfigValueFloat assume positive values.
#   Will need to be modified if we ever need to support a negative config value.

def getConfigValueInt(value, name=''):
    if type(value) == int:
        return value
    elif type(value) == float:
        return int(value)
    else:
        if not value.isdigit():
            raise ValueError('Invalid value for config parameter %s. Should be a positive integer. Got %s' %(name, str(value)))
        return int(value)



FLOAT_RE = re.compile('^(?P<int_part>[\d]*)([\.](?P<decimal_part>[\d]+)){0,1}$')

def getConfigValueFloat(value, name=''):
    if type(value) == float:
        return value
    elif type(value) == int:
        return float(value)
    else:
        if not FLOAT_RE.match(value):
            raise ValueError('Invalid value for config parameter %s. Should be a positive floating-point number. Got %s' %(name, str(value)))
        return float(value)


        
