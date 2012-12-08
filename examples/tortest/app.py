#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
from torext.handlers import _BaseHandler
from torext.route import include

import settings


app = TorextApp(settings, {'LOG_RESPONSE': True})
app.setup()


@app.route('/')
class TestHdr(_BaseHandler):
    def get(self):
        return self.write('get ok')

    def post(self):
        return self.write('post ok')


app.route_many([
    ('/account', include('account.views'))
])

print app.host_handlers


if __name__ == '__main__':

    app.command_line_config()
    app.run()
