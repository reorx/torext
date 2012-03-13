#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '0.1'

from setuptools import setup

setup(
    name='torext',
    version=__version__,
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='http://github.com/nodemix/torext',
    description='torext is an instrumental package which aim at easy implementation of tornado based project',
    packages=[
        'torext',
        'torext.db',
        'torext.handlers',
        'torext.utils',
        'torext.scripts',
    ],
    package_data={
        'torext': [
            'templates/flask_style.py',
            'templates/project/__init__.py',
            'templates/project/app.py',
            'templates/project/settings.py',
        ]
    },
    entry_points={
        'console_scripts': [
            'torext.flake = torext.scripts.syntax_checker:main',
            'torext.sketch = torext.scripts.sketch_maker:main',
        ]
    },
    install_requires=[
        'tornado==2.1.1',
        'pymongo>=2.1',
        'mongokit>=0.7.2',
        'redis>=2.4',
        'pika>=0.9.5',
        'requests>=0.9',
        'pyflakes>=0.5.0',
        'jsonrpclib>=0.1.3',
    ],
)
