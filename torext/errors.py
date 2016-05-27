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


# make_settings.py

class SettingsError(TorextException):
    pass


# app.py

class ArgsParseError(TorextException):
    pass


# script.py

class CommandArgumentError(TorextException):
    pass
