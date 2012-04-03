#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# simplified implementation of server process running
#

import sys
import logging
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from torext import settings, base_settings


def print_service_info():
    tmpl = """\nService Info::
    Project:     {0}
    Port:        {1}
    Processes:   {2}
    Logging:     {3}
    Debug:       {4}
    Locale:      {5}
    url:         {6}
    Connections: {7}
    """
    from torext.connections import connections as conns
    connsText = ''
    for k, v in conns._availables.iteritems():
        connsText += '\n        {0:<10} {1}'.format(k + ':', v)
    if not connsText:
        connsText = '[]'
    s = settings
    project = s.project
    if project == base_settings.project:
        project = project + " (seems you havn't indicated this setting)"
    info = tmpl.format(
        project,
        s.port,
        s.debug and 1 or s.processes,
        s.logging,
        s.debug and 'on' or 'off',
        s.locale,
        'http://127.0.0.1:%s' % s.port,
        connsText)
    logging.info(info)


def run_api_server(app):
    http_server = HTTPServer(app)

    # multiprocess could not be used in debug mode
    if settings.debug:
        http_server.listen(settings.port)
    else:
        http_server.bind(settings.port)
        http_server.start(settings.processes)

    print_service_info()

    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        print '\nStoping the ioloop.. ',
        IOLoop.instance().stop()
        print 'Exit'
        sys.exit()
