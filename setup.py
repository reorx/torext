#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '0.1'

import distutils.core

distutils.core.setup(
    name='torext',
    version=__version__,
    author='Nodemix',
    author_email='novoreorx@gmail.com',
    url='http://nodemix.com',
    description='torext is an instrumental package which aim at easy implementation of tornado based project',
    packages=[
        'torext',
        'torext.handler',
        'torext.utils',
        'torext.scripts',
        'torext.third'
    ],
    package_data = {
        'torext': ['fixtures/base_options.yaml', 
                   'fixtures/custom_options_template.yaml']
    },
    scripts=['bin/torext_syntax'],
)
