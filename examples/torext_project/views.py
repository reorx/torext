#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext_project.base import BaseHandler


class HomeHdr(BaseHandler):
    def get(self):
        self.__class__.visit_count += 1
        self.render('home.html', visit_count=self.__class__.visit_count)


handlers = [
    ('/', HomeHdr),
]
