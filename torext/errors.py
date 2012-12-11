#!/usr/bin/env python
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


# import inspect


class TorextException(Exception):
    pass


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


##
# TODO add `errors` to its attribute
class ParametersInvalid(TorextException):
    pass


class OperationNotAllowed(TorextException):
    pass
##


class SettingUndefined(TorextException):
    pass


class ArgsParseError(TorextException):
    pass


class DatabaseError(TorextException):
    pass
