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

    summary = 'A user service manager for running/managing/monitoring daemons and services'
    try:
        with open('README.rst', 'rt') as f:
            long_description = f.read()
    except Exception as e:
        sys.stderr.write('Error reading from README.rst: %s\n' %(str(e),))
        log_description = summary

    setup(name='usrsvc',
            version='1.0.0',
            packages=['usrsvcmod'],
            scripts=['usrsvc', 'usrsvcd'],
            author='Tim Savannah',
            author_email='kata198@gmail.com',
            maintainer='Tim Savannah',
            url='https://github.com/kata198/AdvancedHTMLParser',
            maintainer_email='kata198@gmail.com',
            requires=['configobj', 'NamedAtomicLock'],
            install_requires=['configobj', 'NamedAtomicLock'],
            description=summary,
            long_description=long_description,
            license='GPLv2',
            keywords=['usrsvc', 'usrsvcd', 'daemon', 'user', 'services', 'service', 'init', 'script', 'start', 'stop', 'restart', 'manage', 'programs', 'applications', 'supervisor', 'supervisord', 'systemd', 'daemontools'],
            classifiers=['Development Status :: 4 - Beta',
                         'Programming Language :: Python',
                         'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                         'Programming Language :: Python :: 2',
                          'Programming Language :: Python :: 2',
                          'Programming Language :: Python :: 2.7',
                          'Programming Language :: Python :: 3',
                          'Programming Language :: Python :: 3.3',
                          'Programming Language :: Python :: 3.4',
                          'Programming Language :: Python :: 3.5',
                          'Topic :: System :: Boot :: Init',
            ]
    )



