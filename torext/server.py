#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# simple implementation of http & socket servers
#

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer


def run_http_server(application, opts):
    http_server = HTTPServer(application)

    # NOTE could not use multiprocess mode under debug
    if opts['debug']:
        http_server.listen(opts['port'])
    else:
        http_server.bind(opts['port'])
        http_server.start(opts['processes'])

    IOLoop.instance().start()

def run_socket_server():
    pass
