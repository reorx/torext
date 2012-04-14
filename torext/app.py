#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from tornado.web import Application as TornadoApplication
from torext import settings


UNLOG_URIS = [
    '/favicon.ico',
]


class TorextApp(TornadoApplication):
    """
    Simplify the way to setup and run an app instance
    """
    def __init__(self, handlers):
        """
        Automatically involves torext's settings
        """
        options = {
            'debug': settings['DEBUG'],
            'logging': settings['LOGGING'],
            'log_function': self.log_function,
        }
        if 'TEMPLATE_PATH' in settings:
            options['template_path'] = settings['TEMPLATE_PATH']
        if 'STATIC_PATH' in settings:
            options['static_path'] = settings['STATIC_PATH']
            options['static_url_prefix'] = settings['STATIC_URL_PREFIX']
            UNLOG_URIS.append(settings['STATIC_URL_PREFIX'])

        super(TorextApp, self).__init__(handlers, **options)

    def log_function(self, handler):
        if handler.get_status() < 400:
            log_method = logging.info
        elif handler.get_status() < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        for i in UNLOG_URIS:
            if handler.request.uri.startswith(i):
                log_method = logging.debug
                break

        request_time = 1000.0 * handler.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)

    def run(self):
        from torext.server import run_server
        run_server(self)
