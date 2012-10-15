#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import torext
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
        if not torext.SETUPED:
            torext.setup()

        http_server = HTTPServer(self)
        if settings['DEBUG']:
            if settings['PROCESSES']:
                logging.info('Multiprocess could not be used in debug mode')
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


def print_service_info():
    tmpl = """\nMode [{0}], Service info::
    Project:         {1}
    Port:            {2}
    Processes:       {3}
    Logging(root):   {4}
    Locale:          {5}
    Debug:           {6}
    url:             {7}
    """

    info = tmpl.format(
        settings['DEBUG'] and 'Debug' or 'Product',
        settings['PROJECT'] or 'None (better be assigned)',
        settings['PORT'],
        settings['DEBUG'] and 1 or settings['PROCESSES'],
        '' in settings['LOGGING'] and settings['LOGGING']['']['level'] or 'None',
        settings['LOCALE'],
        settings['DEBUG'],
        'http://127.0.0.1:%s' % settings['PORT'],
    )

    logging.info(info)
