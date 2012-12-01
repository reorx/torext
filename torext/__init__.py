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
    from torext.log import set_logger

    print 'Setup torext..'

    # setup root logger (as early as possible)
    set_logger('', **settings['LOGGING'])

    # reset timezone
    os.environ['TZ'] = settings['TIME_ZONE']
    time.tzset()

    # add upper folder path to sys.path if not in
    if settings['DEBUG'] and settings._module:
        parent_path = os.path.join(
            os.path.dirname(settings._module.__file__), os.pardir)
        if os.path.abspath(parent_path) in [os.path.abspath(i) for i in sys.path]:
            logging.info('%s is in sys.path, skip adding')
        else:
            sys.path.insert(0, parent_path)
            logging.info('Add %s to sys.path' % os.path.abspath(parent_path))

    # if `PROJECT` is set in settings, project should be importable as a python module
    if settings['PROJECT']:
        try:
            __import__(settings['PROJECT'])
            logging.debug('import %s success' % settings['PROJECT'])
        except ImportError:
            raise ImportError('PROJECT could not be imported, may be app.py is outside the project\
                or there is no __init__ in the package.')

    global SETUPED
    SETUPED = True


def module_config(settings_module):
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
    settings.py is the basis

    if wants to change them by command line arguments,
    the existing option will be transformed to the value type in settings.py
    the unexisting option will be treated as string by default,
    and transform to certain type if `!<type>` was added after the value.

    example:
    $ python app.py --PORT=1000
    """
    import sys

    args = sys.argv[1:]
    args_dict = {}
    existed_keys = []
    new_keys = []

    for t in args:
        if not t.startswith('--'):
            raise errors.ArgsParseError('Bad arg: %s' % t)
        try:
            key, value = tuple(t[2:].split('='))
        except:
            raise errors.ArgsParseError('Bad arg: %s' % t)

        args_dict[key] = value

        if key in settings:
            existed_keys.append(key)
        else:
            new_keys.append(key)

    if existed_keys:
        print 'Changed settings:'
        for i in existed_keys:
            before = settings[i]
            settings[i] = args_dict[i]
            print '  %s  %s (%s)' % (i, args_dict[i], before)

    if new_keys:
        print 'New settings:'
        for i in new_keys:
            settings[i] = args_dict[i]
            print '  %s  %s' % (i, args_dict[i])


class Settings(dict, SingletonMixin):
    """
    Philosophy was borrowed from django.conf.Settings

    As there are just few necessary values involved by tornado.options.options,
    (in httpclient and testing), and options.define is complicate and not convenient to use,
    Settings is created to replace tornado.options.options.

    by import torext module, a Settings object will be instanced and stored globally,
    then it can be involved in any place like this:
    >>> import torext
    >>> print torext.settings
    or
    >>> from torext import settings
    >>> print settings

    getting value from settings is like from a normal dict:
    >>> settings['DEBUG']
    True
    >>> settings.get('PORT')
    8000
    >>> settings.get('WTF', None)
    None

    notice that you can use lower case word to get or set the value:
    >>> settings['debug'] is settings.get('DEBUG')
    True
    >>> settings['port'] = 8765
    >>> settings['PORT']
    8765

    TODO require_setting
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
            try:
                return super(Settings, self).__getitem__(key.lower())
            except KeyError:
                raise errors.SettingUndefined('Setting %s is not defined in settings' % key)

    def __setitem__(self, key, value):
        # for i in key:
        #     if i != i.upper():
        #         raise errors.SettingDefineError('You should always define UPPER CASE VARIABLE as setting')
        super(Settings, self).__setitem__(key.upper(), value)

    def __str__(self):
        return '<Settings. %s >' % dict(self)


settings = Settings.instance()
