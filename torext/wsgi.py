#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import logging
import datetime
import traceback
import gevent.pywsgi as gwsgi


class FormattedWSGIHandler(gwsgi.WSGIHandler):
    logger = logging.getLogger('gevent.wsgi')

    status_level_map = {
        200: logging.INFO,
        300: logging.INFO,
        400: logging.WARNING,
        500: logging.ERROR
    }

    def format_request(self):
        """Override for better log format
        """
        # Tornado format:
        # [INFO 2015-03-24 11:29:57 app:521] 200 GET /static/css/lib/pure-min.css (127.0.0.1) 6.76ms
        # Current format:
        # [gevent.wsgi] INFO 127.0.0.1 - - [2015-03-24 11:18:45] "GET /test HTTP/1.1" 200 304 0.000793
        fmt = '{now} {status} {requestline} ({client_address}) {response_length} {delta}ms'

        data = dict(
            now=datetime.datetime.now().replace(microsecond=0),
            response_length=self.response_length or '-',
            client_address=self.client_address[0] if isinstance(self.client_address, tuple) else self.client_address,
            status=(getattr(self, 'status', None) or '000').split()[0],
            requestline=getattr(self, 'requestline')
        )
        try:
            self._status_int = int(data['status'])
        except ValueError:
            self._status_int = None
        if data['requestline']:
            # Original "GET / HTTP/1.1", remove the "HTTP/1.1"
            data['requestline'] = ' '.join(data['requestline'].split(' ')[:-1])
        else:
            data['requestline'] = '???'
        if self.time_finish:
            delta = '%.2f' % ((self.time_finish - self.time_start) * 1000)
        else:
            delta = '-'
        data['delta'] = delta

        return fmt.format(**data)

        # return '%s - - [%s] "%s" %s %s %s' % (
        #     client_address or '-',
        #     now,
        #     getattr(self, 'requestline', ''),
        #     (getattr(self, 'status', None) or '000').split()[0],
        #     length,
        #     delta)

    def log_request(self):
        if not self.server.log_enabled:
            return

        msg = self.format_request()

        status = self._status_int

        if status < 300:
            flag = 200
        elif status < 400:
            flag = 300
        elif status < 500:
            flag = 400
        else:
            flag = 500
        level = self.status_level_map[flag]

        self.logger.log(level, msg)

    def handle_error(self, type, value, tb):
        """This method copies the code from pywsgi.WSGIHandler.handle_error,
        change the write part to be a reflection of traceback and environ
        """
        if not issubclass(type, gwsgi.GreenletExit):
            self.server.loop.handle_error(self.environ, type, value, tb)
        if self.response_length:
            self.close_connection = True
        else:
            tb_stream = traceback.format_exception(type, value, tb)
            del tb
            tb_stream.append('\n')
            tb_stream.append(pprint.pformat(self.environ))
            body = ''.join(tb_stream)
            headers = gwsgi._INTERNAL_ERROR_HEADERS[:]
            headers[2] = ('Content-Length', str(len(body)))

            self.start_response(gwsgi._INTERNAL_ERROR_STATUS, headers)
            self.write(body)


class WSGIServer(gwsgi.WSGIServer):
    handler_class = FormattedWSGIHandler

    def __init__(self, *args, **kwargs):
        """
        :param bool log_enabled: Indicate whether to log request or not
        """
        # TODO log_enabled replace `log_request` method
        self.log_enabled = True
        if 'log_enabled' in kwargs:
            self.log_enabled = kwargs.pop('log_enabled')
        super(WSGIServer, self).__init__(*args, **kwargs)
