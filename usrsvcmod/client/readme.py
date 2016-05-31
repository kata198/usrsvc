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

    This class prints the readme contents, which are loaded by setup.py
'''

# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :

import sys

try:
    from usrsvcmod.client._readme_contents import README_CONTENTS
except ImportError:
    README_CONTENTS = "Extended help not available -- usrsvc was not installed correctly.\n"

def printReadme(outObj=None):
    if outObj is None:
        outObj = sys.stdout
    
    sys.stdout.write(README_CONTENTS)
    sys.stdout.flush()


# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :
