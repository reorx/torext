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
    def __init__(self, msg):
        self.msg = msg
        # self.caller_name = inspect.stack()[1][3]
        super(TorextException, self).__init__(msg)

    # def __str__(self):
        # return 'From %s() : %s' % (self.caller_name, self.msg)


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
