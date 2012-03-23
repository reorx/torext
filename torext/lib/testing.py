#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# use nose for testing. eg. nosetest test_general.py

import logging
from unittest import TestCase


class _TestCase(TestCase):
    # no need to indicate level because logs of all level will be displayed by nose
    logger_name = 'testcase'

    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.logger_name)
        return self._logger
