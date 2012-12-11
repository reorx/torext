#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.web import Application, RequestHandler
from tornado.options import enable_pretty_logging
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from torext.handlers.rpc import JSONRPCHandler

import logging
logging.getLogger().setLevel(logging.DEBUG)
enable_pretty_logging()

class HomeHdr(RequestHandler):
    def get(self):
        return self.write('yes')


class RPCHdr(JSONRPCHandler):
    def add(self, x, y):
        return x + y

    def err(self):
        return self


http_server = HTTPServer(Application([(r'/', HomeHdr), (r'/rpc', RPCHdr)], debug=True))
http_server.listen(10001)

io_loop = IOLoop.instance()
io_loop.start()
