#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from torext.log import set_logger
from nose.tools import with_setup
from torext.compat import PY2


def test_logging():
    msgs = [
        '中文 utf8',
        '始める utf8',
    ]
    if PY2:
        msgs += [
            u'中文 gbk'.encode('gbk'),
            u'中文 unicode',
            u'始める shift_jis'.encode('shift_jis'),
            u'始める unicode',
        ]
    for i in msgs:
        yield do_logging, i


def logging_setup():
    set_logger('')


def logging_teardown():
    logging.getLogger().handlers = []


@with_setup(logging_setup, logging_teardown)
def do_logging(msg):
    logging.info(msg)
