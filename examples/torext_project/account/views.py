#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.handlers import _BaseHandler


class AHdr(_BaseHandler):
    def get(self):
        self.write('/account/a')


handlers = [
    ('/a', AHdr)
]
