#!/usr/bin/env python
# -*- coding: utf-8 -*-


class TorextException(Exception):
    def __init__(self, message=''):
        if isinstance(message, str):
            message = message.decode('utf8')
        self.message = message

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.message


# route.py

class URLRouteError(TorextException):
    """error in router"""


# params.py

class ValidationError(TorextException):
    """
    error occur when validating values
    """
    def __init__(self, description=None, error_message=None):
        self.description = description
        self.error_message = error_message

    def __unicode__(self):
        #return '%s (%s)' % (self.description, self.error_message) if self.error_message else self.description
        return self.description or self.error_message

    def __repr__(self):
        return str(self)


class ParamsInvalidError(TorextException):
    def __init__(self, errors):
        """Make sure no string only unicode in errors"""
        if isinstance(errors, list):
            self.errors = errors
        else:
            self.errors = [errors, ]

    def __unicode__(self):
        return u'Invalid params: %s' % self.errors


# script.py

class CommandArgumentError(TorextException):
    pass


# make_settings.py

class SettingsError(TorextException):
    pass


# app.py

class ArgsParseError(TorextException):
    pass


# sql.py

class DoesNotExist(TorextException):
    pass
