#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

class BaseError(Exception):
    def __init__(self, msg):
        self.msg = msg
        logging.error('error:: {0}, {1}'.format(self.__class__.__name__, msg))

    def __str__(self):
        return 'exception:: %s: %s' % (self.__class__.__name__, self.msg)

class ConnectionError(BaseError): pass

class OperationError(BaseError): pass
