#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.compat import decode_, PY2


class TorextException(Exception):
    def __init__(self, message=''):
        if isinstance(message, str):
            message = decode_(message, 'utf8')
        self.message = message

    if PY2:
        def __str__(self):
            return self.__unicode__().encode('utf-8')

        def __unicode__(self):
            return self.message


# route.py

class URLRouteError(TorextException):
    """error in router"""


# make_settings.py

class SettingsError(TorextException):
    pass


# app.py

class ArgsParseError(TorextException):
    pass


# script.py

class CommandArgumentError(TorextException):
    pass
