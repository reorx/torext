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


def print_service_info():
    tmpl = """\nService Info::
    Name:       {0}
    Port:       {1}
    Processes:  {2}
    Logging:    {3}
    Debug:      {4}
    Locale:     {5}
    Connections:{6}
    """
    from torext.db.connections import connections as conns
    connsText = ''
    for k, v in conns._availables.iteritems():
        connsText += '\n        {0:<10} {1}'.format(k + ':', v)
    s = settings
    info = tmpl.format(
        s.package,
        s.application['port'],
        s.application['debug'] and 1 or s.application['processes'],
        s.logging,
        s.application['debug'] and 'on' or 'off',
        s.application['locale'],
        connsText)
    logging.info(info)


def run_api_server(app):
    opts = settings.application
    http_server = HTTPServer(app)

    # NOTE could not use multiprocess mode under debug
    if opts['debug']:
        http_server.listen(opts['port'])
    else:
        http_server.bind(opts['port'])
        http_server.start(opts['processes'])

    print_service_info()
    IOLoop.instance().start()


def run_web_server(app, opts):
    # print_service_info()
    pass
