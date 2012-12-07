#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
from torext.handlers import _BaseHandler

import settings


class TestHdr(_BaseHandler):
    def get(self):
        return self.write('post ok')

    def post(self):
        return self.write('post ok')


app = TorextApp(settings, {'LOG_RESPONSE': True})

app.add_handler('/', TestHdr)


if __name__ == '__main__':

    app.command_line_config()
    app.run()
