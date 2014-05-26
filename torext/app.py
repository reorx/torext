#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import copy
import socket
import logging

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application

from torext import settings
from torext import errors
from torext.testing import TestClient, AppTestCase
from torext.log import set_logger, set_nose_formatter
from torext.route import Router
from torext.utils import json_encode, json_decode


class TorextApp(object):
    """
    Simplify the way to setup and run an app instance
    """
    current_app = None

    def __init__(self, settings_module=None, extra_settings=None,
                 application_options=None, httpserver_options=None,
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
            XHEADERS
        """
        if settings_module:
            self.module_config(settings_module)
        if extra_settings:
            self.update_settings(extra_settings)
        self._application_options = application_options
        self._httpserver_options = httpserver_options
        self.io_loop = io_loop
        self.is_setuped = False
        self.handlers = []
        self.default_host = '.*$'
        self.host_handlers = {
            self.default_host: []
        }
        self.application = None
        self.project = None
        self.uimodules = {}
        self.json_encoder = json_encode
        self.json_decoder = json_decode

        global settings
        self.settings = settings

        TorextApp.current_app = self

    def update_settings(self, incoming, convert_type=False, log_changes=False):
        global settings

        def _log(s):
            if log_changes:
                print s

        for i in incoming:
            incoming_v = incoming[i]

            if i in settings:
                _log('Settings update "%s": %s -> %s' % (i, settings[i], incoming_v))

                if convert_type:
                    incoming_v = _convert_type(incoming_v, settings[i])
            else:
                _log('Settings add "%s": %s' % (i, incoming_v))

            settings[i] = incoming_v

        self.is_setuped = False

        # Config logger here so that it can be done as early as possible,
        # and reflect as soon as possible each time relevant settings changed.
        logging_config = self._get_logging_config()
        set_logger('', **logging_config)
        logging.debug('logging config: %s', logging_config)

    def _get_logging_config(self):
        logging_config = settings['LOGGING_OPTIONS'].copy()
        logging_config['level'] = settings['LOGGING']
        return logging_config

    def set_root_path(self, root_path=None, settings_module=None):
        """
        root_path will only be used for 3 situations:
        1. fix ``static_path`` and ``template_path``
        2. check project's directory name with the value in settings.PROJECT
        3. append parent path to sys.path
        """
        if root_path:
            self.root_path = root_path
            return

        if settings_module:
            self.root_path = os.path.dirname(os.path.abspath(settings_module.__file__))
            return

        # try to guess which module import app.py
        import inspect

        caller = inspect.stack()[1]
        caller_module = inspect.getmodule(caller[0])
        assert hasattr(caller_module, '__file__'), 'Caller module %s should have __file__ attr' % caller_module
        self.root_path = os.path.dirname(os.path.abspath(caller_module.__file__))

    def get_httpserver_options(self):
        keys = ('xheaders', )
        options = {}
        for k in keys:
            k_upper = k.upper()
            if k_upper in settings:
                options[k] = settings[k_upper]

        if self._httpserver_options:
            for k, v in self._httpserver_options.iteritems():
                options[k] = v

        return options

    def get_application_options(self):
        # TODO full list options
        options_keys = [
            'debug',
            'static_path',
            'template_path',
            'cookie_secret',
            'log_function',
            'ui_modules',
            'static_handler_class',
            'static_handler_args',
        ]
        options = {
            'log_function': _log_function,
            'ui_modules': self.uimodules,
        }

        for k in options_keys:
            k_upper = k.upper()
            if k_upper in settings:
                options[k] = settings[k_upper]

        if hasattr(self, 'root_path'):
            self._fix_paths(options)

        if self._application_options:
            for k, v in self._application_options.iteritems():
                options[k] = v

        return options

    def _fix_paths(self, options):
        """
        fix `static_path` and `template_path` to be absolute
        path according to self.root_path so that PWD can be ignoreed.
        """
        for k in ('template_path', 'static_path'):
            if k in options:
                v = options.pop(k)
                if not os.path.isabs(v):
                    v = os.path.abspath(
                        os.path.join(self.root_path, v))
                    logging.debug('Fix %s to be absolute: %s' % (k, v))
                options[k] = v

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

    def route_many(self, *args, **kwargs):
        """
        >>> from torext.route import include
        >>> app = TorextApp()
        >>> app.route_many([
        ...     ('/account', include('account.views')),
        ...     ('/account', include('account.views')),
        ... ], '^account.example.com$')
        """
        if len(args) == 2:
            prefix, rules = args
        elif len(args) == 1:
            prefix = None
            rules = args[0]
        else:
            raise ValueError('The amount of args of route_many method can only be one or two')
        router = Router(rules, prefix=prefix)
        self.add_handlers(router.get_handlers(), host=kwargs.get('host'))

    def add_handlers(self, handlers, host=None):
        handlers_container = self._get_handlers_on_host(host)
        handlers_container[0:0] = handlers

    def module_config(self, settings_module):
        """
        Optional function
        """
        assert hasattr(settings_module, '__file__'), 'settings must be a module'
        # set root_path according to module file
        self.set_root_path(settings_module=settings_module)
        logging.debug('Set root_path: %s', self.root_path)

        global settings

        self.update_settings(dict(
            [(i, getattr(settings_module, i)) for i in dir(settings_module)
             if not i.startswith('_') and i == i.upper()]))

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

        NOTE This method is deprecated, use `torext.script` to parse command line arguments instead.
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
            logging.debug('Changed settings:')
            for i in existed_keys:
                before = settings[i]
                type_ = type(before)
                if type_ is bool:
                    if args_dict[i] == 'True':
                        _value = True
                    elif args_dict[i] == 'False':
                        _value = False
                    else:
                        raise errors.ArgsParseError('%s should only be True or False' % i)
                else:
                    _value = type_(args_dict[i])
                settings[i] = _value
                logging.debug('  %s  [%s]%s (%s)', i, type(settings[i]), settings[i], before)

        if new_keys:
            logging.debug('New settings:')
            for i in new_keys:
                settings[i] = args_dict[i]
                logging.debug('  %s  %s', i, args_dict[i])

        # NOTE if ``command_line_config`` is called, logging must be re-configed
        self.update_settings({})

    def setup(self):
        """This function will be called both before `run` and testing started.
        """
        testing = settings.get('TESTING')

        if testing:
            # Fix nose handler in testing situation.
            logging_config = self._get_logging_config()
            set_nose_formatter(logging_config)
            print 'testing, set nose formatter: %s' % logging_config

        # reset timezone
        os.environ['TZ'] = settings['TIME_ZONE']
        time.tzset()

        # determine project name
        if settings._module:
            project = os.path.split(self.root_path)[1]
            if settings['PROJECT']:
                assert settings['PROJECT'] == project, 'PROJECT specialized in settings (%s) '\
                    'should be the same as project directory name (%s)' % (settings['PROJECT'], project)
            else:
                settings['PROJECT'] = project

        # PROJECT should be importable as a python module
        if settings['PROJECT']:
            # add upper directory path to sys.path if not in
            if settings._module:
                _abs = os.path.abspath
                parent_path = os.path.dirname(self.root_path)
                if not _abs(parent_path) in [_abs(i) for i in sys.path]:
                    sys.path.insert(0, parent_path)
                    logging.info('Add %s to sys.path' % _abs(parent_path))
            try:
                __import__(settings['PROJECT'])
                logging.debug('import package `%s` success' % settings['PROJECT'])
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

        application = self._make_application()

        http_server_options = self.get_httpserver_options()
        http_server = HTTPServer(application, io_loop=self.io_loop, **http_server_options)
        listen_kwargs = {}
        if settings.get('ADDRESS'):
            listen_kwargs['address'] = settings.get('ADDRESS')
        if not settings['TESTING'] and settings['DEBUG']:
            if settings['PROCESSES'] and settings['PROCESSES'] > 1:
                logging.info('Multiprocess could not be used in debug mode')
            try:
                http_server.listen(settings['PORT'], **listen_kwargs)
            except socket.error, e:
                logging.warning('socket.error detected on http_server.listen, set ADDRESS="0.0.0.0" in settings to avoid this problem')
                raise e
        else:
            try:
                http_server.bind(settings['PORT'], **listen_kwargs)
            except socket.error, e:
                logging.warning('socket.error detected on http_server.listen, set ADDRESS="0.0.0.0" in settings to avoid this problem')
                raise e
            http_server.start(settings['PROCESSES'])

        self.http_server = http_server
        self.application = application

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
        content = '\nMode %s, Service Info:' % mode

        info = {
            'Project': settings['PROJECT'] or 'None (better be assigned)',
            'Port': settings['PORT'],
            'Processes': settings['DEBUG'] and 1 or settings['PROCESSES'],
            'Logging(root) Level': settings['LOGGING'],
            'Locale': settings['LOCALE'],
            'Debug': settings['DEBUG'],
            'Home': 'http://127.0.0.1:%s' % settings['PORT'],
        }

        #if settings['DEBUG']:
        buf = []
        for host, rules in self.application.handlers:
            buf.append(host.pattern)
            for i in rules:
                buf.append('  ' + i.regex.pattern)
        info['URL Patterns(by sequence)'] = '\n    ' + '\n    '.join(buf)

        for k in ['Project', 'Port', 'Processes',
                  'Logging(root) Level', 'Locale', 'Debug', 'Home', 'URL Patterns(by sequence)']:
            content += '\n- %s: %s' % (k, info[k])

        logging.info(content)

    def test_client(self, **kwgs):
        return TestClient(self, **kwgs)

    @property
    def TestCase(_self):
        class CurrentTestCase(AppTestCase):
            def get_client(self):
                return _self.test_client()
        return CurrentTestCase

    def register_uimodules(self, **kwargs):
        self.uimodules.update(kwargs)

    def register_json_encoder(self, encoder_func):
        self.json_encoder = encoder_func
        return encoder_func

    def register_json_decoder(self, decoder_func):
        self.json_decoder = decoder_func
        return decoder_func

    def register_application_configurator(self, config_func):
        self.application_configurator = config_func
        return config_func

    def _make_application(self, application_class=Application):
        options = self.get_application_options()
        logging.debug('%s settings: %s', application_class.__name__, options)

        # this method intended to be able to called for multiple times,
        # so attributes should not be changed, just make a copy
        host_handlers = copy.copy(self.host_handlers)
        top_host_handlers = host_handlers.pop('.*$')
        application = application_class(top_host_handlers, **options)

        if host_handlers:
            for host, handlers in host_handlers.iteritems():
                application.add_handlers(host, handlers)

        # call `application_configurator` to do extra setups
        self.application_configurator(application)
        return application

    def application_configurator(self, *args, **kwargs):
        pass

    def wsgi_application(self):
        from tornado.wsgi import WSGIApplication
        return self._make_application(application_class=WSGIApplication)


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
    return _caller_path


def guess():
    return _guess_caller()


def _convert_type(raw, before):
    type_ = type(before)
    if type_ is bool:
        if raw == 'True':
            value = True
        elif raw == 'False':
            value = False
        else:
            raise errors.ArgsParseError('Should only be True or False, got: %s' % raw)
    else:
        value = type_(raw)
    return value
