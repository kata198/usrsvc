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
