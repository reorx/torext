#!/usr/bin/env python
# -*- coding: utf-8 -*-


import string
import logging
import torext
from torext.handlers import _BaseHandler
from torext.app import SettingsBasedApplication
from torext.server import run_api_server
from torext import settings


class FlaskStyleApp(object):
    def __init__(self, brand):
        self.brand = brand
        self.handlers = {}
        self.settings = settings
        torext.initialize()

    def _hdr_name(self, url):
        digit = 3
        prefix = self.brand
        suffix = 'Hdr'
        body = ''.join([i for i in url if i in string.letters])
        num = len(self.handlers)
        if len(str(num)) < digit:
            body += (digit - len(str(num))) * '0' + str(num)
        else:
            body += str(num)
        return prefix + body + suffix

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
            # exec 'class %s(_BaseHandler): pass' % hdr_name in globals(), locals()
            # hdr = locals()[hdr_name]
            hdr = type(hdr_name, (_BaseHandler, ), {})
            self.handlers[url] = hdr

        def route_adaptor(fn):
            setattr(hdr, method, fn)
            # hold a reference of app on the funciton
            fn.app = self
            return fn
        return route_adaptor

    def run(self):
        run_api_server(
            SettingsBasedApplication(
                handlers=[i for i in self.handlers.iteritems()],
            )
        )


if __name__ == '__main__':
    app = FlaskStyleApp('demoapp')
    app.settings.set('debug', True)

    @app.route('get', '/')
    def hello(hdr):
        hdr.write('ok')

    logging.info(hello)
    logging.info(hello.app)

    @app.route('post', '/user/profile')
    def hello_post(hdr):
        hdr.write('ok post')

    app.run()
