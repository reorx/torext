#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import torext
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application as TornadoApplication

from torext import settings
from torext.handlers import _BaseHandler


class TorextApp(TornadoApplication):
    """
    Simplify the way to setup and run an app instance
    """
    def __init__(self, handlers):
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
        # transmit settings values to a new dict with its key lower cased.
        kwgs = {}
        for k in settings:
            kwgs[k.lower()] = settings[k]
        # reassign log_function
        kwgs['log_function'] = self.log_function
        super(TorextApp, self).__init__(handlers, **kwgs)

    def log_function(self, handler):
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

    def run(self):
        if not torext.SETUPED:
            torext.setup()

        http_server = HTTPServer(self)
        if settings['DEBUG']:
            if settings['PROCESSES'] and settings['PROCESSES'] > 1:
                logging.info('Multiprocess could not be used in debug mode')
            http_server.listen(settings['PORT'])
        else:
            http_server.bind(settings['PORT'])
            http_server.start(settings['PROCESSES'])

        log_service_info()

        try:
            IOLoop.instance().start()
        except KeyboardInterrupt:
            print '\nStopping ioloop.. ',
            IOLoop.instance().stop()
            print 'Exit'
            sys.exit(0)


def log_service_info():
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


class FlaskStyleApp(object):
    def __init__(self, project_name):
        self.project_name = project_name
        self.handlers = {}
        self.settings = settings
        self._app = TorextApp
        self.counter = 0

    def _hdr_name(self, url):
        name = '%s%s' % (self.project_name, self.counter)
        self.counter += 1
        return name

    def _no_endslash_url(self, url):
        if url.endswith('/'):
            return url[-1:]
        return url

    def route(self, method, url):
        url = self._no_endslash_url(url)
        hdr_name = self._hdr_name(url)
        logging.debug(hdr_name)

        if url in self.handlers:
            hdr = self.handlers[url]
        else:
            hdr = type(hdr_name, (_BaseHandler, ), {})
            self.handlers[url] = hdr

        def route_adaptor(fn):
            setattr(hdr, method, fn)
            # hold a reference of app on the funciton
            fn.app = self
            return fn
        return route_adaptor

    def run(self):
        self._app = TorextApp(
            handlers=[i for i in self.handlers.iteritems()],
        )
        self._app.run()

if __name__ == '__main__':
    app = FlaskStyleApp('demoapp')
    app.settings['DEBUG'] = True
    app.settings['PORT'] = 8002

    @app.route('get', '/')
    def hello(hdr):
        hdr.write('ok')

    logging.info(hello)
    logging.info(hello.app)

    @app.route('post', '/user/profile')
    def hello_post(hdr):
        hdr.write('ok post')

    app.run()
