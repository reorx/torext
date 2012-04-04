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


class TorextException(Exception):
    def __init__(self, msg):
        self.msg = msg
        logging.debug(self.msg)

    def __str__(self):
        return self.msg


class URLRouteError(TorextException):
    """
    error in router
    """
    pass


class ConnectionError(TorextException):
    """
    error occurs in connection
    """
    pass


class ValidationError(TorextException):
    """
    error occur when validating values
    """
    pass


class AuthenticationNotPass(TorextException):
    pass


class ObjectNotFound(TorextException):
    pass


class MultiObjectsReturned(TorextException):
    pass


class ParametersInvalid(TorextException):
    pass


class SettingUndefined(TorextException):
    pass
