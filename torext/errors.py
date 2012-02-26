#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
errors:

    ConnectionError

    ValidationError

    AuthenticationNotPass

    ObjectNotFound

    MultiObjectsReturned

    ParametersInvalid
"""


import logging
from tornado.web import HTTPError

HTTPError = HTTPError


class TorextBaseException(Exception):
    def __init__(self, msg):
        self.msg = msg
        logging.debug(self.msg)

    def __str__(self):
        return self.msg


class ConnectionError(TorextBaseException):
    """
    error occurs in connection
    """
    pass


class ValidationError(TorextBaseException):
    """
    error occur when validating values
    """
    pass


class AuthenticationNotPass(TorextBaseException):
    pass


class ObjectNotFound(TorextBaseException):
    pass


class MultiObjectsReturned(TorextBaseException):
    pass


class ParametersInvalid(TorextBaseException):
    pass
