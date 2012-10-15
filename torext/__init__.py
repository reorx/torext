#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.6'

from torext import errors
from torext.utils import SingletonMixin


SETUPED = False


def setup():
    """
    setups before run
    """
    import os
    import sys
    import time
    import logging
    from torext.logger import set_logger

    print 'Setup torext..'

    # set loggers
    if '' in settings['LOGGING']:
        set_logger('', **settings['LOGGING'][''])
        logging.info('RootLogger has been set')
    for name, opts in settings['LOGGING'].iteritems():
        if name == 'root':
            continue
        set_logger(name, **opts)

    # reset timezone
    os.environ['TZ'] = settings['TIME_ZONE']
    time.tzset()

    if settings['DEBUG'] and settings._module:

        parent_path = os.path.join(
            os.path.dirname(settings._module.__file__), os.pardir)
        sys.path.insert(0, parent_path)

    # if `PROJECT` was set in settings,
    # means project should be able to imported as a python module
    if settings['PROJECT']:
        try:
            __import__(settings['PROJECT'])
            logging.debug('import %s success' % settings['PROJECT'])
        except ImportError:
            raise ImportError('PROJECT could not be imported, may be app.py is outside the project\
                or there is no __init__ in the package.')

    global SETUPED
    SETUPED = True


def pyfile_config(settings_module):
    """
    Optional function
    """
    assert hasattr(settings_module, '__file__'), 'settings passed in initialize() must be a module'

    global settings

    for i in dir(settings_module):
        if not i.startswith('_'):
            settings[i] = getattr(settings_module, i)

    settings._module = settings_module


def command_line_config():
    """
    settings.py is the basement

    if wants to change them by command line arguments,
    the existing option will be transformed to the value type in settings.py
    the unexisting option will be treated as string by default,
    and force to type if `!<type>` was added after

    format:
        python app.py --PORT 1000
    """
    import sys

    args = sys.argv[1:]

    if not len(args) % 2 == 0:
        raise errors.ArgsParseError('Bad args: length of args is not multiple of 2')

    def to_tuple_list(l):
        tl = []
        while l:
            tl.append((l.pop(0), l.pop(0)))
        return tl

    args = to_tuple_list(args)

    args_dict = {}
    existed_keys = []
    new_keys = []

    for t in args:
        if not t[0].startswith('--') or not t[0].upper() == t[0]:
            raise errors.ArgsParseError('Bad arg: %s %s' % t)
        key = t[0][2:]
        args_dict[key] = t[1]

        if key in settings:
            existed_keys.append(key)
        else:
            new_keys.append(key)

    if existed_keys:
        print 'Changed settings:'
        for i in existed_keys:
            print '  %s  %s (%s)' % (i, settings[i], args_dict[i])
            settings[i] = args_dict[i]

    if new_keys:
        print 'New settings:'
        for i in new_keys:
            print '  %s  %s' % (i, args_dict[i])
            settings[i] = args_dict[i]


class Settings(dict, SingletonMixin):
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

        self._module = None

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
