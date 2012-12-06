#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application

from torext.utils import SingletonMixin
from torext import errors


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


class TorextApp(object):
    """
    Simplify the way to setup and run an app instance
    """
    def __init__(self, settings_module=None, application_options={}):
        """
        Automatically involves torext's settings

        related keys:
            DEBUG
            TEMPLATE_PATH
            STATIC_PATH
            STATIC_URL_PREFIX
            STATIC_HANDLER_CLASS
            STATIC_HANDLER_ARGS
            COOKIE_SECRET
            XSRF_COOKIES
            UI_MODULES
            UI_METHODS
            GZIP
        """
        if settings_module:
            self.module_config(settings_module)
        self._application_options = application_options
        self.is_setuped = False
        self.handlers = []
        self.application = None
        self.root_path = None
        self.settings = settings

    def get_application_options(self):
        # TODO full list options
        options = {
            'debug': True,
            'static_path': None,
            'template_path': None,
            'cookie_secret': None,
            'log_function': _log_function
        }

        for k in options:
            k_upper = k.upper()
            if k_upper in settings:
                options[k] = settings[k_upper]

        for k, v in self._application_options.iteritems():
            if not k in options:
                raise ValueError('%s in application_options is not a proper one' % k)
            options[k] = v

        return options

    def add_handler(self, url, handler):
        self.handlers.insert(0, (url, handler))

    def run(self):
        if not self.is_setuped:
            self.setup()

        self.application = Application(self.handlers, **self.application_options)
        http_server = HTTPServer(self.application)
        if settings['DEBUG']:
            if settings['PROCESSES'] and settings['PROCESSES'] > 1:
                logging.info('Multiprocess could not be used in debug mode')
            http_server.listen(settings['PORT'])
        else:
            http_server.bind(settings['PORT'])
            http_server.start(settings['PROCESSES'])

        self.log_app_info()

        try:
            IOLoop.instance().start()
        except KeyboardInterrupt:
            print '\nStopping ioloop.. ',
            IOLoop.instance().stop()
            print 'Exit'
            sys.exit(0)

    def setup(self):
        """
        setups before run
        """
        import os
        import time
        import logging
        from torext.log import set_logger

        print 'Setup torext..'

        # setup root logger (as early as possible)
        set_logger('', **settings['LOGGING'])

        # reset timezone
        os.environ['TZ'] = settings['TIME_ZONE']
        time.tzset()

        if settings._module:
            file_path = settings._module.__file__
        else:
            import inspect
            caller = inspect.stack()[1]
            caller_module = inspect.getmodule(caller[0])
            file_path = caller_module.__file__
        self.root_path = os.path.dirname(file_path)

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

        self.application_options = self.get_application_options()

        self.is_setuped = True

    def module_config(self, settings_module):
        """
        Optional function
        """
        assert hasattr(settings_module, '__file__'), 'settings passed in initialize() must be a module'

        global settings

        for i in dir(settings_module):
            if not i.startswith('_'):
                settings[i] = getattr(settings_module, i)

        settings._module = settings_module

    def command_line_config(self):
        """
        settings.py is the basis

        if wants to change them by command line arguments,
        the existing option will be transformed to the value type in settings.py
        the unexisting option will be treated as string by default,
        and transform to certain type if `!<type>` was added after the value.

        example:
        $ python app.py --PORT=1000
        """

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

    def log_app_info(self):
        mode = settings['DEBUG'] and 'Debug' or 'Product'
        info = '\nMode %s, Service Info:' % mode

        info_dic = {
            'Project': settings['PROJECT'] or 'None (better be assigned)',
            'Port': settings['PORT'],
            'Processes': settings['DEBUG'] and 1 or settings['PROCESSES'],
            'Logging(root) Level': settings['LOGGING']['level'],
            'Locale': settings['LOCALE'],
            'Debug': settings['DEBUG'],
            'Home': 'http://127.0.0.1:%s' % settings['PORT'],
        }

        for k in ['Project', 'Port', 'Processes',
                  'Logging(root) Level', 'Locale', 'Debug', 'Home']:
            info += '\n- %s: %s' % (k, info_dic[k])

        logging.info(info)


def _log_function(handler):
    """
    override Applicaion.log_function so that what to log can be controled.
    """
    if handler.get_status() < 400:
        log_method = logging.info
    elif handler.get_status() < 500:
        log_method = logging.warning
    else:
        log_method = logging.error
    for i in settings['LOGGING_IGNORE_URLS']:
        if handler.request.uri.startswith(i):
            log_method = logging.debug
            break

    request_time = 1000.0 * handler.request.request_time()
    log_method("%d %s %.2fms", handler.get_status(),
               handler._request_summary(), request_time)
