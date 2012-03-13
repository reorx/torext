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

project = 'torext_powered'

locale = 'en_US'


# variables below can be redefined by commend line options

processes = 1

port = 8000

debug = False

logging = 'INFO'



###########
# optional

# third_lib = 'third'

# template_path = 'web/template'
