#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from unittest import TestCase
from . import logger


class _TestCase(TestCase):
    _logger_name = 'testcase'

    def _setup_logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self._logger_name)
        if not self._logger.handlers or\
            self._logger.handlers[0].formatter._fmt != logger.FORMATS['testcase']:
                logger.enable_logger(self._logger_name, level=logging.INFO, fmt=logger.FORMATS['testcase'])

    def _log(self, msg):
        self._setup_logger()
        self._logger.info(msg)
