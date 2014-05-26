#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Always stay on 0.9 before documentation is finished
__version__ = '0.9.4'

from setuptools import setup

with open('README.rst', 'r') as f:
    description = f.read()

setup(
    license='License :: OSI Approved :: MIT License',
    name='torext',
    version=__version__,
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='http://github.com/reorx/torext',
    description="The missing tornado mate",
    long_description=description,
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
