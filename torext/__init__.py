#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import logging

ENV_VAR_NAME = 'TOREXT_SETTINGS_MODULE'


def initialize(settings_module):
    if settings_module is None:
        pass
    # NOTE [20120214] discard this step.
    # step 0. use settings_module find and add project parent path to sys.path,
    # to ensure project can be imported
    # sys.path.insert(0,
    #     os.path.abspath(
    #         os.path.join(
    #             os.path.dirname(settings_module.__file__), '..')))

    # step 0. add torext/third to sys.path
    sys.path.insert(0,
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'third')))

    # setp 1. set torext using settings (internally used in torext)
    global settings
    settings._configure(settings_module)

    # setp 2. set logging
    from torext.logger import BaseFormatter
    root_logger = logging.getLogger()
    if not isinstance(settings.logging, int):
        level = getattr(logging, settings.logging.upper())
    else:
        level = settings.logging
    print 'logging level: ', level
    root_logger.setLevel('INFO')
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(BaseFormatter(color=True))
    root_logger.addHandler(streamHandler)

    # setp 3. configure connections
    if hasattr(settings, 'connections'):
        from torext.db.connections import connections
        connections.configure(settings.connections)


########################################
# borrow way from django.conf.Settings #
########################################

class Settings(object):
    """docstring for Settings"""

    def __init__(self):
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
