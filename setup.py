#!/usr/bin/env python
'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv2.

    You should have received a copy of this with the source distribution as LICENSE,
    otherwise the most up to date license can be found at
    https://github.com/kata198/usrsvc/LICENSE

    A user service manager for running/managing/monitoring daemons and services
'''

import os
import sys
from setuptools import setup


if __name__ == '__main__':

    dirName = os.path.dirname(__file__)
    if dirName and os.getcwd() != dirName:
        os.chdir(dirName)

    summary = 'A service manager for running/managing/monitoring/auto-restarting daemons and services at the user (non-root) level'

    # Use README.rst for the long_description ( for pypi )
    try:
        with open('README.rst', 'rt') as f:
            long_description = f.read()
    except Exception as e:
        sys.stderr.write('Error reading from README.rst: %s\n' %(str(e),))
        long_description = summary

    # Use README.md (actually looks sane uninterpreted) as the --readme option.
    try:
        with open('README.md', 'rt') as f:
            readme_description = f.read()
    except Exception as e:
        sys.stderr.write('Error reading from README.rst: %s\n' %(str(e),))
        readme_description = summary


    try:
        with open('usrsvcmod/client/_readme_contents.py', 'wt') as f:
            f.write('README_CONTENTS = """%s"""\n' %(readme_description,)  )
            f.flush()
            try:
                os.fsync(f)
            except:
                pass
    except Exception as e:
        sys.stderr.write('Warning, failed to update readme.py - extended help will not be available.\n')
        sys.stderr.write(str(e)  +  '\n')

    setup(name='usrsvc',
            version='1.5.11',
            packages=['usrsvcmod', 'usrsvcmod.Monitoring', 'usrsvcmod.client'],
            scripts=['usrsvc', 'usrsvcd'],
            author='Tim Savannah',
            author_email='kata198@gmail.com',
            maintainer='Tim Savannah',
            url='https://github.com/kata198/usrsvc',
            maintainer_email='kata198@gmail.com',
            requires=['configobj', 'NamedAtomicLock', 'func_timeout'],
            install_requires=['configobj', 'NamedAtomicLock>=1.1.0', 'func_timeout', 'python-subprocess2'],
            description=summary,
            long_description=long_description,
            license='GPLv2',
            keywords=['usrsvc', 'usrsvcd', 'daemon', 'user', 'services', 'service', 'init', 'script', 'start', 'stop', 'restart', 'manage', 'programs', 'applications', 'supervisor', 'supervisord', 'systemd', 'daemontools'],
            classifiers=['Development Status :: 5 - Production/Stable',
                         'Programming Language :: Python',
                         'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                         'Programming Language :: Python :: 2',
                          'Programming Language :: Python :: 2',
                          'Programming Language :: Python :: 2.7',
                          'Programming Language :: Python :: 3',
                          'Programming Language :: Python :: 3.3',
                          'Programming Language :: Python :: 3.4',
                          'Programming Language :: Python :: 3.5',
                          'Programming Language :: Python :: 3.6',
                          'Topic :: System :: Boot :: Init',
            ]
    )



