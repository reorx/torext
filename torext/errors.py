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


class ValidationError(TorextException):
    """
    error occur when validating values
    """
    def __init__(self, description=None, error_message=None):
        self.description = description
        self.error_message = error_message

    def __str__(self):
        #return '%s (%s)' % (self.description, self.error_message) if self.error_message else self.description
        return self.description or self.error_message

    def __repr__(self):
        return self.__str__()


class AuthenticationNotPass(TorextException):
    pass


##
# TODO add `errors` to its attribute
class ParamsInvalidError(TorextException):
    def __init__(self, error_s):
        if isinstance(error_s, list):
            self.errors = error_s
        else:
            self.errors = [error_s, ]

    def __str__(self):
        return 'Invalid params: %s' % self.errors


class CommandArgumentError(TorextException):
    pass


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
