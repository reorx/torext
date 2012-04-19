#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '1.3'
# ENVIRONMENT_KEY = 'TOREXT_SETTINGS_MODULE'

import logging
from torext.lib.logger import configure_logger
from torext.conns import configure_conns
from torext.lib.utils import OneInstanceObject
from torext import errors


def initialize(settings_module):
    assert hasattr(settings_module, '__file__'), 'settings passed in initialize( must be a module'

    configure_settings_from_module(settings_module)

    args = configure_settings_from_commandline()

    # logger config should be as early as possible
    configure_logger('',
        level=getattr(logging, settings['LOGGING']),
        handler_options={
            'type': 'stream',
            'color': True,
            'fmt': settings['LOGGING_FORMAT'],
        })

    configure_environ(settings_module)

    if 'CONNS' in settings:
        configure_conns(settings['CONNS'])

    if len(args) > 0:
        if args[0] == 'shell':
            import sys
            from torext.lib.shell import start_shell
            start_shell()
            sys.exit()


def configure_settings_from_module(settings_module):
    global settings

    for i in dir(settings_module):
        if not i.startswith('_'):
            settings[i] = getattr(settings_module, i)


def configure_settings_from_commandline():
    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-p', '--PORT', type='int')
    parser.add_option('-l', '--LOGGING', type='str')
    parser.add_option('-P', '--PROCESSES', type='int')
    parser.add_option('-d', '--DEBUG', action='store_true', default=None)
    options, args = parser.parse_args()

    for k, v in options.__dict__.iteritems():
        if v is not None:
            settings[k] = v

    return args


def configure_environ(settings_module):
    """
    make some environmental change with settings file
    """
    import os
    import sys

    _abs = os.path.abspath
    _join = os.path.join
    to_adds = []

    project_path = os.path.dirname(settings_module.__file__)
    parent_path = _join(project_path, os.pardir)
    to_adds.append(parent_path)

    if 'THIRD_LIB' in settings:
        lib_path = _join(project_path, settings['THIRD_LIB'])
        assert os.path.exists(lib_path), 'the third_lib you indicated is not exist'
        to_adds.append(lib_path)

    for path in to_adds:
        path = _abs(path)
        if not path in [_abs(i) for i in sys.path]:
            sys.path.insert(0, path)

    # check importings
    try:
        __import__(settings['PROJECT'])
        logging.debug('try to import %s' % settings['PROJECT'])
    except ImportError:
        raise ImportError('PROJECT could not be imported, may be app.py is outside the project\
            and you havn`t add project parent path to sys.path yet')


class Settings(dict, OneInstanceObject):
    """
    Philosophy was borrow from django.conf.Settings

    As there are just few things involved by tornado.options.options,
    httpclient and testing, they are all uncommon modules and do little in project.
    also, tornado options is not convenient to use. So I decide to create a new
    object called Settings instead of options. Settings file writting will be
    much eaiser and comfortable for pycoders.

    NOTE settings object is internally used in torext and the project
    """
    def __init__(self):
        """
        Setting definitions in base_settings are indispensable
        """
        from torext import base_settings

        for i in dir(base_settings):
            if not i.startswith('_'):
                self[i] = getattr(base_settings, i)

    def __getitem__(self, key):
        try:
            return super(Settings, self).__getitem__(key)
        except KeyError:
            raise errors.SettingUndefined('Setting %s is not defined in settings' % key)

    def __setitem__(self, key, value):
        for i in key:
            if i != i.upper():
                raise errors.SettingDefineError('You should always define UPPER CASE VARIABLE as setting')
        super(Settings, self).__setitem__(key, value)

    def __str__(self):
        return '<Settings. %s >' % dict(self)


settings = Settings.instance()
