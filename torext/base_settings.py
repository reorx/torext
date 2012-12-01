#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# variables in this module are essential basements of settings,
# the priority sequence of base_settings.py, settings.py(in project), and cmd options is::
#   1. commandline arguments
#   2. settings.py
#   3. base_settings.py


#############
# necessary #
#############

PROJECT = None

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

LOGGING = {
    'level': 'INFO',
    'propagate': 1,
    'color': True
}

LOG_REQUEST = False

LOG_RESPONSE = False

LOG_RESPONSE_LINE_LIMIT = 0

TIME_ZONE = 'Asia/Shanghai'

STATIC_PATH = 'static'

TEMPLATE_PATH = 'template'

LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]


############
# optional #
############

# COOKIE_SECRET = 'P0UTa5iuRaaVlV8QZF2uVR7hHwTOSkQhg2Fol18OKwc='

# SECURE_COOKIE = ''
# SECURE_HEADER = ''
