#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012 reorx xiao

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__version__ = '1.3'

from setuptools import setup

setup(
    license='License :: OSI Approved :: MIT License',
    name='torext',
    version=__version__,
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='http://github.com/nodemix/torext',
    description='torext is an instrumental package which aim at easy implementation of tornado based project',
    packages=[
        'torext',
        'torext.lib',
        'torext.mongodb',
        'torext.handlers',
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
            'torext.flake = torext.scripts.syntax:main',
            'torext.sketch = torext.scripts.sketch:main',
        ]
    },
    install_requires=[
        'tornado>=2.1.1',
        'pymongo>=2.1',
        'requests>=0.9'
    ],
)
