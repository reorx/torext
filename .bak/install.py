#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# NOTE: this script require setuptools (easy_install) to run properly
# NOTE current not use, only if manually-install module is required will this script be useful
#

import os
import ConfigParser
from distutils.version import StrictVersion

config = ConfigParser.RawConfigParser()
config.read('install.cfg')
for name, version in config.items('requirements'):
    # version may be parsed as float, its nesessary to transform it
    version = str(version)
    try:
        pkg = __import__(name)
        _version = getattr(pkg, '__version__', None) or\
                   getattr(pkg, 'VERSION', None) or\
                   getattr(pkg, 'version', None)
        if '|' in version:
            version, name = tuple(version.split('|'))
        if _version is None:
            print 'Could not get package version informaion, will force upgrade'
            os.system('easy_install -U %s' % name)
            continue
        if StrictVersion(version) > _version:
            print 'version number is low (%s > %s), upgrade package' %\
                    (version, _version)
            os.system('easy_install -U %s' % name)

    except ImportError:
        print 'missing package:', name
        os.system('easy_install %s' % name)
    else:
        print 'satisfied: %s %s' % (name, _version)

os.system('python setup.py install')
