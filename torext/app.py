#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application as TornadoApplication

from torext import settings


class TorextApp(TornadoApplication):
    """
    Simplify the way to setup and run an app instance
    """
    def __init__(self, handlers):
        """
        Automatically involves torext's settings
        """
        kwgs = {
            'debug': settings['DEBUG'],
            'logging': settings['LOGGING'],
            'log_function': self.log_function,
        }
        if 'TEMPLATE_PATH' in settings:
            kwgs['template_path'] = settings['TEMPLATE_PATH']
        if 'STATIC_PATH' in settings:
            kwgs['static_path'] = settings['STATIC_PATH']
            if 'STATIC_URL_PREFIX' in settings:
                kwgs['static_url_prefix'] = settings['STATIC_URL_PREFIX']
        if 'COOKIE_SECRET' in settings:
            kwgs['cookie_secret'] = settings['COOKIE_SECRET']

        super(TorextApp, self).__init__(handlers, **kwgs)

    def log_function(self, handler):
        if handler.get_status() < 400:
            log_method = logging.info
        elif handler.get_status() < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        for i in settings['UNLOG_URLS']:
            if handler.request.uri.startswith(i):
                log_method = logging.debug
                break

        request_time = 1000.0 * handler.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)

    def run(self):
        prepare()

        http_server = HTTPServer(self)
        if settings['DEBUG']:
            if settings['PROCESSES']:
                print 'Multiprocess could not be used in debug mode'
            http_server.listen(settings['PORT'])
        else:
            http_server.bind(settings['PORT'])
            http_server.start(settings['PROCESSES'])

        print_service_info()

        try:
            IOLoop.instance().start()
        except KeyboardInterrupt:
            print '\nStoping the ioloop.. ',
            IOLoop.instance().stop()
            print 'Exit'
            sys.exit()


def prepare():
    """
    preparations before run
    """
    configure_logger('',
        level=getattr(logging, settings['LOGGING']),
        handler_options={
            'type': 'stream',
            'color': True,
            'fmt': settings['LOGGING_FORMAT'],
        }
    )

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
            print 'import %s success' % settings['PROJECT']
        except ImportError:
            raise ImportError('PROJECT could not be imported, may be app.py is outside the project\
                or there is no __init__ in the package.')


def print_service_info():
    tmpl = """\nMode [{0}], Service info::
    Project:     {1}
    Port:        {2}
    Processes:   {3}
    Logging:     {4}
    Locale:      {5}
    Debug:       {6}
    url:         {7}
    """

    info = tmpl.format(
        settings['DEBUG'] and 'Debug' or 'Product',
        settings['PROJECT'] or 'None (better be assigned)',
        settings['PORT'],
        settings['DEBUG'] and 1 or settings['PROCESSES'],
        settings['LOGGING'],
        settings['LOCALE'],
        settings['DEBUG'],
        'http://127.0.0.1:%s' % settings['PORT'],
    )

    logging.info(info)
