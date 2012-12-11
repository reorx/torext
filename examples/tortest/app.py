#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from torext.app import TorextApp
from torext.handlers import _BaseHandler
from torext.route import include

import settings


app = TorextApp(settings, {'LOG_RESPONSE': True})
app.setup()


class BaseHandler(_BaseHandler):
    def json_error(self, code, error=None):
        """
        """
        msg = {'code': code}
        if isinstance(error, Exception):
            # NOTE(maybe) if use __str__() it will cause UnicodeEncodeError when error contains Chinese unicode
            msg['error'] = str(error)
            logging.info('Get error to write: %s - %s' %
                         (error.__class__.__name__, error))
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.set_status(code)
        self.json_write(msg, code=code)


@app.route('/')
class TestHdr(BaseHandler):
    def get(self):
        return self.write('get ok')

    def post(self):
        return self.write('post ok')


@app.route('/sourcecode')
class SourcecodeHdr(BaseHandler):
    def get(self):
        pass


app.route_many([
    ('/account', include('account.views'))
])

print app.host_handlers


if __name__ == '__main__':

    app.command_line_config()
    app.run()
