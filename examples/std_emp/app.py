#!/usr/bin/python
# -*- coding: utf-8 -*-

import torext
from torext import settings
from torext.app import TorextApp
from torext.handlers import _BaseHandler, api_define


class HomeHdr(_BaseHandler):
    def get(self):
        self.write(str(dir(self.request)))


class ApiHdr(_BaseHandler):
    @api_define([
        ('name'),
        ('age', int)
    ])
    def get(self):
        self.write(self.params)


if __name__ == '__main__':
    torext.initialize()
    settings['DEBUG'] = True

    app = TorextApp([
        (r'/', HomeHdr),
        (r'/api', ApiHdr)
    ])
    app.run()
