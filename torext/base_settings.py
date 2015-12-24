#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# variables in this module are essential basements of settings,
# the priority sequence of base_settings.py, settings.py(in project), and cmd options is::
#   1. commandline arguments
#   2. settings.py
#   3. base_settings.py


#############
# essential #
#############

PROJECT = None

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

AUTORELOAD = True

SERVE_TRACEBACK = True

STATIC_PATH = 'static'

TEMPLATE_PATH = 'template'

TEMPLATE_ENGINE = 'tornado'

LOGGERS = {
    '': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',
        #'fmt': '[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    }
}

LOG_REQUEST = False

LOG_RESPONSE = False

LOG_RESPONSE_LINE_LIMIT = 0

LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]

TESTING = False

TIME_ZONE = 'Asia/Shanghai'


############
# optional #
############

# COOKIE_SECRET = 'P0UTa5iuRaaVlV8QZF2uVR7hHwTOSkQhg2Fol18OKwc='

# SECURE_COOKIE = ''
# SECURE_HEADER = ''
