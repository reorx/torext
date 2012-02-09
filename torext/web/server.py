#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# simple implementation of the main 3 servers
#    api
#    rpc
#    web
#

import logging
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer

from torext import settings


def run_api_server(application):
    opts = settings.application
    http_server = HTTPServer(application)

    # NOTE could not use multiprocess mode under debug
    if opts['debug']:
        http_server.listen(opts['port'])
    else:
        http_server.bind(opts['port'])
        http_server.start(opts['processes'])

    logging.info('api server starting')
    IOLoop.instance().start()


def run_rpc_server(application, opts):
    pass


def run_web_server(application, opts):
    pass
