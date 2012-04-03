#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '1.1'


# temporarily not used
ENV_VAR_NAME = 'TOREXT_SETTINGS_MODULE'


from .errors import SettingUndefined
from . import base_settings


def initialize(settings_module=None):
    import os
    import sys
    # import logging
    import optparse

    # settings
    global settings
    if settings_module:
        assert hasattr(settings_module, '__file__'), 'settings passed in initialize( must be a module'
        settings._configure(settings_module)

    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type='int')
    parser.add_option('-l', '--logging', type='str')
    parser.add_option('-P', '--processes', type='int')
    parser.add_option('-d', '--debug', action='store_true', default=False)
    options, args = parser.parse_args()
    for k, v in options.__dict__.iteritems():
        if v is not None:
            settings.set(k, v)

    # sys.path
    if settings_module:
        to_adds = []
        project_path = os.path.abspath(
                        os.path.dirname(settings_module.__file__))
        parent_path = os.path.abspath(
                        os.path.join(project_path, '..'))
        to_adds.append(parent_path)
        if settings.has('third_lib'):
            lib_path = os.path.abspath(
                        os.path.join(project_path, settings.third_lib))
            assert os.path.exists(lib_path), 'the third_lib you indicated is not exist'
            to_adds.append(lib_path)
        for path in to_adds:
            if not path in [os.path.abspath(i) for i in sys.path]:
                sys.path.insert(0, path)

    # logging
    from torext.lib.logger import enable_logger
    enable_logger('', level=settings.logging, color=True)

    # connections
    if settings.has('connections'):
        from torext.connections import connections
        connections.configure(settings.connections)


class Settings(object):
    """
    Philosophy was borrow from django.conf.Settings

    As there are just a few things involved by tornado.options.options,
    httpclient and testing, they are all uncommon modules and do little in project.
    also, tornado options is not convenient to use. So I decide to create a new
    object called Settings instead of options. Settings file writting will be
    much eaiser and comfortable for pycoders.

    NOTE settings object is internally used in torext and the project
    """
    def __init__(self):
        """
        Setting definitions in base_settings are indispensable
        """
        for setting in dir(base_settings):
            if not setting.startswith('_'):
                self.set(setting, getattr(base_settings, setting))

    def _configure(self, settings_module):
        """
        settings_module will be checked before passed into this method,
        there is no need to check it again.
        """
        for setting in dir(settings_module):
            if not setting.startswith('_'):
                self.set(setting, getattr(settings_module, setting))

        self._settings_module = settings_module

    def has(self, key):
        return hasattr(self, key)

    def set(self, key, value):
        setattr(self, key, value)

    def __get__(self, key):
        if not self.has(key):
            raise SettingUndefined(key)
        return getattr(self, key)

    def __str__(self):
        ks = self.__dict__.keys()
        for i in ('_settings_module', ):
            if i in ks:
                ks.remove(i)
        return '<Settings. keys: %s >' % ks

settings = Settings()
