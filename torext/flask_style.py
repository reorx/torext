#!/usr/bin/python
# -*- coding: utf-8 -*-


import string
import logging
from tornado.web import RequestHandler, Application
from tornado.ioloop import IOLoop


class FlaskStyleApp(object):
    def __init__(self, brand):
        self.brand = brand
        self.handlers = {}

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

    def route(self, method, url):
        hdr_name = self._hdr_name(url)
        logging.debug(hdr_name)
        if url in self.handlers:
            hdr = self.handlers[url]
        else:
            exec 'class %s(RequestHandler): pass' % hdr_name in globals(), locals()
            hdr = locals()[hdr_name]
            self.handlers[url] = hdr

        def route_adaptor(fn):
            setattr(hdr, method, fn)
        return route_adaptor

    def run(self):
        app = Application(
            [i for i in self.handlers.iteritems()],
            debug=True
        )
        app.listen(19010)
        IOLoop.instance().start()


if __name__ == '__main__':
    app = FlaskStyleApp('justTest')

    @app.route('get', '/')
    def hello(hdr):
        hdr.write('ok')

    @app.route('post', '/user/profile')
    def hello_post(hdr):
        hdr.write('ok post')

    app.run()
