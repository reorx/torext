#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
errors:

    ConnectionError

    ValidationError

    AuthenticationNotPass

    ObjectNotFound

    MultiObjectsReturned

    ParamsInvalidError
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
    def __init__(self, description=None, error_message=None):
        self.description = description
        self.error_message = error_message

    def __str__(self):
        return self.description or self.error_message

    def __repr__(self):
        return self.__str__()


class AuthenticationNotPass(TorextException):
    pass


class ObjectNotFound(TorextException):
    pass


class MultipleObjectsReturned(TorextException):
    pass


##
# TODO add `errors` to its attribute
class ParamsInvalidError(TorextException):
    def __init__(self, params):
        self.params = params

    def __str__(self):
        return 'Invalid params: %s' % self.params


class OperationNotAllowed(TorextException):
    pass


class OperationFailed(TorextException):
    pass


class SettingsError(TorextException):
    pass


class ArgsParseError(TorextException):
    pass


class DatabaseError(TorextException):
    pass


class JSONDecodeError(TorextException):
    pass
