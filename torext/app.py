#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application

from torext import settings
from torext import errors
from torext.log import set_logger, set_nose_formatter
from torext.route import Router


class TorextApp(object):
    """
    Simplify the way to setup and run an app instance
    """
    def __init__(self, settings_module=None, extra_settings={}, application_options={},
                 io_loop=None):
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
        self.update_settings(extra_settings)
        self._application_options = application_options
        self.io_loop = io_loop
        self.is_setuped = False
        self.handlers = []
        self.default_host = ".*$"
        self.host_handlers = {
            self.default_host: []
        }
        self.application = None
        self.root_path = None
        self.project = None

        global settings
        self.settings = settings

    def update_settings(self, incoming):
        global settings
        for i in incoming:
            settings[i] = incoming[i]

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

        if self._application_options:
            for k, v in self._application_options.iteritems():
                options[k] = v

        return options

    def _get_handlers_on_host(self, host=None):
        if not host:
            handlers = self.host_handlers[self.default_host]
        else:
            self.host_handlers.setdefault(host, [])
            handlers = self.host_handlers[host]
        return handlers

    def route(self, url, host=None):
        """This is a decorator
        """
        def fn(handler_cls):
            handlers = self._get_handlers_on_host(host)
            handlers.insert(0, (url, handler_cls))
            return handler_cls
        return fn

    def route_many(self, rules, host=None):
        """
        >>> app.route_many([
                ('/account', include('account.views')),
                ('/account', include('account.views')),
            ], '^account.example.com$')
        """
        router = Router(rules)
        self.add_handlers(router.get_handlers(), host)

    def add_handlers(self, handlers, host=None):
        handlers_container = self._get_handlers_on_host(host)
        handlers_container[0:0] = handlers

    def module_config(self, settings_module):
        """
        Optional function
        """
        assert hasattr(settings_module, '__file__'), 'settings passed in initialize() must be a module'

        global settings

        self.update_settings(dict(
            [(i, getattr(settings_module, i)) for i in dir(settings_module)
             if not i.startswith('_')]))

        settings._module = settings_module

        # keep a mapping to app on settings object
        settings._app = self

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

    def setup(self):
        """
        setups before run, it recommended to call this method in the project's app.py

        it will:
        """
        testing = settings.get('TESTING')

        if not testing:
            print 'Setup torext..'

        # setup root logger (as early as possible)
        if testing:
            set_nose_formatter(settings['LOGGING'])
        else:
            set_logger('', **settings['LOGGING'])

        # reset timezone
        os.environ['TZ'] = settings['TIME_ZONE']
        time.tzset()

        # get root path
        if settings._module:
            self.root_path = os.path.dirname(os.path.abspath(settings._module.__file__))
        else:
            global _caller_path
            self.root_path = os.path.dirname(_caller_path)

        # determine project name
        if settings._module:
            project = os.path.split(self.root_path)[1]
            if settings['PROJECT']:
                assert settings['PROJECT'] == project, 'PROJECT specialized in settings (%s) '\
                    'should be the same as project directory name (%s)' % (settings['PROJECT'], project)
            else:
                settings['PROJECT'] = project

        # add upper directory path to sys.path if not in
        if settings['DEBUG'] and settings._module:
            _abs = os.path.abspath
            parent_path = os.path.dirname(self.root_path)
            if not _abs(parent_path) in [_abs(i) for i in sys.path]:
                sys.path.insert(0, parent_path)
                if not testing:
                    logging.info('Add %s to sys.path' % _abs(parent_path))

        #rl = logging.getLogger()
        #logging.info('root logger handlers: %s' % rl.handlers)

        # PROJECT should be importable as a python module
        if settings['PROJECT']:
            try:
                __import__(settings['PROJECT'])
                if not testing:
                    logging.debug('import %s success' % settings['PROJECT'])
            except ImportError:
                raise ImportError('PROJECT could not be imported, may be app.py is outside the project'
                                  'or there is no __init__ in the package.')

        self.is_setuped = True

    def _init_infrastructures(self):
        if self.io_loop:
            if not self.io_loop.initialized():
                # this means self.io_loop is a customized io_loop, so `install` should be called
                # to make it the singleton instance
                #print self.io_loop.__class__.__name__
                self.io_loop.install()
        else:
            self.io_loop = IOLoop.instance()

        self.application = Application(**self.get_application_options())
        for host, handlers in self.host_handlers.iteritems():
            self.application.add_handlers(host, handlers)

        http_server = HTTPServer(self.application, io_loop=self.io_loop)
        if not settings['TESTING'] and settings['DEBUG']:
            if settings['PROCESSES'] and settings['PROCESSES'] > 1:
                logging.info('Multiprocess could not be used in debug mode')
            http_server.listen(settings['PORT'])
        else:
            http_server.bind(settings['PORT'])
            http_server.start(settings['PROCESSES'])

        self.http_server = http_server

    @property
    def is_running(self):
        if self.io_loop:
            return self.io_loop._running
        return False

    def run(self):
        if not self.is_setuped:
            self.setup()

        self._init_infrastructures()

        if not settings.get('TESTING'):
            self.log_app_info()

        try:
            self.io_loop.start()
        except KeyboardInterrupt:
            print '\nStopping ioloop.. ',
            IOLoop.instance().stop()
            print 'Exit'
            sys.exit(0)

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

    def test_client(self):
        from torext.testing import TestClient
        return TestClient(self)


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


_caller_path = None


def _guess_caller():
    """
    try to guess which module import app.py
    """
    import inspect
    global _caller_path

    caller = inspect.stack()[1]
    caller_module = inspect.getmodule(caller[0])
    if hasattr(caller_module, '__file__'):
        _caller_path = os.path.abspath(caller_module.__file__)

_guess_caller()
