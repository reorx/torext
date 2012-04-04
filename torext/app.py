#!/usr/bin/python
# -*- coding: utf-8 -*-

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
        }
        if 'TEMPLATE_PATH' in settings:
            options['template_path'] = settings['TEMPLATE_PATH']

        super(TorextApp, self).__init__(handlers, **options)

    def log_request(self, handler, *args, **kwgs):
        if handler.request.uri in UNLOG_URIS:
            return
        super(TorextApp, self).log_request(handler, *args, **kwgs)

    def run(self):
        from torext.server import run_server
        run_server(self)
