#!/usr/bin/python
# -*- coding: utf-8 -*-

class BaseError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'exception:: %s: %s' % (self.__class__.__name__, self.msg)
