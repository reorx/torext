#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.3'
# ENVIRONMENT_KEY = 'TOREXT_SETTINGS_MODULE'

import logging
from torext.lib.logger import configure_logger
from torext.conns import configure_conns
from torext.lib.utils import OneInstanceObject
from torext import errors


INITIALIZED = False


def initialize(settings_module=None):
    if settings_module:
        assert hasattr(settings_module, '__file__'), 'settings passed in initialize( must be a module'

        configure_settings_from_module(settings_module)

        configure_environ(settings_module)

    configure_settings_from_commandline()

    # logger config should be as early as possible
    configure_logger('',
        level=getattr(logging, settings['LOGGING']),
        handler_options={
            'type': 'stream',
            'color': True,
            'fmt': settings['LOGGING_FORMAT'],
        }
    )

    if 'CONNS' in settings:
        configure_conns(settings['CONNS'])

    global INITIALIZED
    INITIALIZED = True


def configure_settings_from_module(settings_module):
    global settings

    for i in dir(settings_module):
        if not i.startswith('_'):
            settings[i] = getattr(settings_module, i)


def configure_settings_from_commandline():
    """
    settings.py is the basement
    
    if wants to change them by command line arguments,
    the existing option will be transformed to the value type in settings.py
    the unexisting option will be treated as string by default,
    and force to type if `!<type>` was added after

    format:
        python app.py settings:port=1000^int;logging=str
    """
    import re
    import sys
    from .errors import CommandArgParseError

    # recurse settings key-value
    settings_cmd_keys = []
    for i in settings:
        settings_cmd_keys.append(i.lower())

    args = {
        'existed': {},
        'new': {}
    }
    args_str = None
    for i in sys.argv[1:]:
        if i.startswith('settings:'):
            args_str = i.lstrip('settings:')
            break
    # print 'sys argv ', sys.argv
    if args_str:
        # print 'get args_str', args_str
        try:
            for i in args_str.split(','):
                kvs = i.split('=')
                if not len(kvs) == 2 or not kvs[0] or not kvs[1]:
                    raise CommandArgParseError('Bad key-value: %s' % i)
                k, v = kvs[0].upper(), kvs[1]
                if k in settings:
                    v_type = type(settings[k.upper()])
                    if v_type is bool:
                        try:
                            v = bool(int(v))
                        except ValueError:
                            _bool_strs = {
                                'True': True,
                                'False': False
                            }
                            if v in _bool_strs:
                                v = _bool_strs[v]
                            else:
                                v = True
                    else:
                        try:
                            v = v_type(v)
                        except Exception, e:
                            raise CommandArgParseError('Bad value: %s, %s' % (v, e))
                    args['existed'][k] = v
                else:
                    if not re.search(r'[A-Z_]+', k):
                        raise CommandArgParseError('Bad key: %s' % k)
                    force_types = {
                        'int': int,
                        'str': str
                    }
                    if len(v) > 4 and v[-4] == '^':
                        type_str = v[-3:]
                        v = v[:-4]
                        if type_str not in force_types:
                            raise CommandArgParseError('Bad value type: %s' % v)
                        try:
                            v = force_types[type_str](v)
                        except Exception, e:
                            raise CommandArgParseError('Bad value: %s, %s' % (v, e))
                    args['new'][k] = v
        except CommandArgParseError, e:
            print '\nError: %s' % e
            print '       Failed to get settings from commandline,'
            print '       continue running, settings not changed.'
            return

        # print 'args dict', args

        print '\nSettings changed by commandline:'

        for k, v in args['existed'].iteritems():
            settings[k] = v
            print ' - %s = %s    (existed)' % (k, v)
        for k, v in args['new'].iteritems():
            settings[k] = v
            print ' - %s = %s    (new)' % (k, v)


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

    # if `PROJECT` was set in settings,
    # means project should be able to imported as a python module
    if settings['PROJECT']:
        try:
            __import__(settings['PROJECT'])
            logging.debug('try to import %s' % settings['PROJECT'])
        except ImportError:
            raise ImportError('PROJECT could not be imported, may be app.py is outside the project\
                and you havn`t add project parent path to sys.path yet')


class Settings(dict, OneInstanceObject):
    """
    Philosophy was borrowed from django.conf.Settings

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
