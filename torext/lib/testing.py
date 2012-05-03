#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# use nose for testing. eg. nosetest test_general.py

import logging
import inspect
from unittest import TestCase


class Log(object):
    """
    when using nosetest, a '<nose.plugins.logcapture.MyMemoryHandler object at 0x2f3e210>' handler
    will be added to root logger, this handler show a feature that if no error occured,
    logs will not be displayed on stderr (shell stream), so we create a logger named 'testcase',
    it will not pass log to root logger, and will handle logs itself, bound to method 'show'
    """
    def __init__(self):
        self.quiet_logger = logging.getLogger()
        self.quiet_logger.setLevel('DEBUG')

        self.show_logger = logging.getLogger('testcase')
        self.show_logger.propagate = 0
        self.show_logger.setLevel('DEBUG')
        hdr = logging.StreamHandler()
        hdr.setFormatter(logging.Formatter())
        self.show_logger.addHandler(hdr)

    def quiet(self, msg, level='INFO'):
        self.quiet_logger.log(getattr(logging, level, 10), msg)

    def show(self, msg, level='INFO'):
        caller_name = inspect.stack()[1][3]
        msg = '\n[%s] %s' % (caller_name, msg)
        self.show_logger.log(getattr(logging, level, 10), msg)


class _TestCase(TestCase):
    log = Log()
