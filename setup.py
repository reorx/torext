#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Always stay on 0.9 before documentation is finished
__version__ = '0.9.2'

from setuptools import setup

setup(
    license='License :: OSI Approved :: MIT License',
    name='torext',
    version=__version__,
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='http://github.com/reorx/torext',
    # TODO replace with README.rst later
    description='torext is an instrumental package which aim at easy implementation of tornado based project',
    packages=[
        'torext',
        'torext.handlers',
        'torext.scripts',
        'torext.test',
    ],
    package_data={
        'torext': [
            'templates/project/__init__.py',
            'templates/project/app.py',
            'templates/project/settings.py',
        ]
    },
    entry_points={
        'console_scripts': [
            'torext-sketch = torext.scripts.sketch:main',
        ]
    },
    install_requires=[
        'tornado>=3.0'
    ],
)
