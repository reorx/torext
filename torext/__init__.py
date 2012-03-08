#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import optparse

ENV_VAR_NAME = 'TOREXT_SETTINGS_MODULE'


def initialize(settings_module):
    assert hasattr(settings_module, '__file__'), 'settings passed in initialize( must be a module'

    # NOTE [20120214] discard this step.
    # step 0. use settings_module find and add project parent path to sys.path,
    # to ensure project can be imported
    # sys.path.insert(0,
    #     os.path.abspath(
    #         os.path.join(
    #             os.path.dirname(settings_module.__file__), '..')))

    # setp 1. reset settings from file and command line options
    global settings
    settings._configure(settings_module)

    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type='int')
    parser.add_option('-l', '--logging', type='str')
    parser.add_option('-d', '--debug', action='store_false', default=True)
    parser.add_option('-P', '--processes', type='int')
    options, args = parser.parse_args()
    for k, v in options.__dict__.iteritems():
        if v is not None:
            setattr(settings, k, v)

    # 0. add third-party lib to sys.path from project
    project_path = os.path.abspath(os.path.dirname(settings_module.__file__))
    lib_path = os.path.join(project_path, settings.third_lib)
    assert os.path.exists(lib_path), 'the third_lib you indicated is not exist'
    sys.path.insert(0, os.path.abspath(lib_path))

    # 2. set logging
    # NOTE before logging is set detaily(eg. add a handler), it will be added
    # a handler automatically if it was used (eg. logging.debug)
    from torext.logger import BaseFormatter
    root_logger = logging.getLogger()
    if not isinstance(settings.logging, int):
        level = getattr(logging, settings.logging.upper())
    else:
        level = settings.logging
    root_logger.setLevel(level)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(BaseFormatter(color=True))
    root_logger.handlers = []  # to ensure no unexpected handler is on root logger
    root_logger.addHandler(streamHandler)

    # 3. configure connections
    if hasattr(settings, 'connections'):
        from torext.db.connections import connections
        connections.configure(settings.connections)


class Settings(object):
    """
    Philosophy was borrow from django.conf.Settings

    NOTE settings object is internally used in torext and project
    """
    def __init__(self):
        """
        Setting definitions in base_settings are indispensable
        """
        from torext import base_settings
        for setting in dir(base_settings):
            if not setting.startswith('_'):
                setattr(self, setting, getattr(base_settings, setting))

    def _configure(self, settings_module):
        for setting in dir(settings_module):
            if not setting.startswith('_'):
                setattr(self, setting, getattr(settings_module, setting))

        self._settings_module = settings_module

settings = Settings()
