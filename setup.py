#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '0.1'

from setuptools import setup

setup(
    name='torext',
    version=__version__,
    author='Nodemix',
    author_email='novoreorx@gmail.com',
    url='http://nodemix.com',
    description='torext is an instrumental package which aim at easy implementation of tornado based project',
    packages=[
        'torext',
        'torext.db',
        'torext.web',
        'torext.web.handlers',
        'torext.utils',
        'torext.scripts',
        'torext.third'
    ],
    package_data = {
        'torext': ['fixtures/base_options.yaml', 
                   'fixtures/custom_options_template.yaml']
    },
    scripts=['bin/torext_syntax'],

    install_requires=[
        'tornado==2.1.1',
        'pymongo>=2.1',
        'mongokit>=0.7.2',
        'redis>=2.4',
        'pika>=0.9.5',
        'requests>=0.9',
        'pyflakes>=0.5.0',
        'jsonrpclib>=0.1.3',
        'tweepy'
    ]
)
