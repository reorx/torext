#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# variables in this module are essential basements of settings,
# the priority sequence of base_settings.py, settings.py(in project), and cmd options is::
#   1. cmd options
#   2. settings.py
#   3. base_settings.py
#
# only if no definition in 1 and 2 will setting in 3 become effective.


################
# indispensable

PROJECT = None

LOCALE = 'en_US'


# variables below can be redefined by commend line options

PROCESSES = 1

PORT = 8000

DEBUG = False

LOGGING = 'INFO'

LOGGING_FORMAT = ' %(message)s'



###########
# optional

# THIRD_LIB = 'third'

# TEMPLATE_PATH = 'web/template'

# CONNS = {}

# could generated a new one by 'torext.lib.hashs.generate_cookie_secret()'
# COOKIE_SECRET = ''

# SECURE_COOKIE = ''
# SECURE_HEADER = ''
