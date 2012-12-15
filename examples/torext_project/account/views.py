#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext_project.base import BaseHandler


class AccountHdr(BaseHandler):
    def get(self):
        self.write(self.request.uri)


class AHdr(BaseHandler):
    def get(self):
        self.write(self.request.uri)


handlers = [
    ('/?', AccountHdr),
    ('/a', AHdr)
]
