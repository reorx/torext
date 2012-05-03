#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# simplified implementation of server process running
#

import sys
import logging
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from torext import settings


def print_service_info(app):
    tmpl = """\nMode [{0}], Service info::
    Project:     {1}
    Port:        {2}
    Processes:   {3}
    Logging:     {4}
    Locale:      {5}
    Debug:       {6}
    url:         {7}
    Connections: {8}
    """
    from torext.conns import conns
    conns_str = ''

    for k, v in conns._container.iteritems():
        conns_str += '\n        {0:<10} {1}'.format(k + ':', v)

    info = tmpl.format(
        settings['DEBUG'] and 'Debug' or 'Production',
        settings['PROJECT'] or 'None (better be assigned)',
        settings['PORT'],
        settings['DEBUG'] and 1 or settings['PROCESSES'],
        settings['LOGGING'],
        settings['LOCALE'],
        settings['DEBUG'],
        'http://127.0.0.1:%s' % settings['PORT'],
        conns_str or '[]'
    )

    logging.info(info)


def run_server(app):
    http_server = HTTPServer(app)

    # multiprocess could not be used in debug mode
    if settings['DEBUG']:
        http_server.listen(settings['PORT'])
    else:
        http_server.bind(settings['PORT'])
        http_server.start(settings['PROCESSES'])

    print_service_info(app)

    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        print '\nStoping the ioloop.. ',
        IOLoop.instance().stop()
        print 'Exit'
        sys.exit()
