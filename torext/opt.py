#!/usr/bin/python
# -*- coding: utf-8 -*-

import yaml
from tornado.options import options
from tornado.options import define as define_option


def parse_and_set(path):
    global options
    for i, o in yaml.load(file(path)).iteritems():
        if i in options:
            options[i].set(o)
        else:
            define_option(i, o)
