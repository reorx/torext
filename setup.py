#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


# Always stay on 0.9 before documentation is finished
__version__ = '0.9.4-r5'


def get_requires():
    with open('requirements.txt', 'r') as f:
        requires = [i for i in map(lambda x: x.strip(), f.readlines()) if i]
    return requires


def get_long_description():
    try:
        with open('README.md', 'r') as f:
            return f.read()
    except IOError:
        return ''


setup(
    license='License :: OSI Approved :: MIT License',
    name='torext',
    version=__version__,
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='http://github.com/reorx/torext',
    description="The missing tornado mate",
    long_description=get_long_description(),
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
    install_requires=get_requires(),
)
