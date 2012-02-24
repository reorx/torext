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


class TorextBaseException(Exception):
    def __init__(self, msg):
        self.msg = msg
        self.__str = '%s %s' % (self.__class__.__name__, self)
        logging.debug(self.__str)

    def __str__(self):
        return self.__str


# class OperationError(TorextBaseException):
#     pass


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
