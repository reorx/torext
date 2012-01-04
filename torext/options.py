#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import yaml
import logging

from tornado.options import options
from tornado.options import define as define_option
from tornado.options import enable_pretty_logging

def parse_options(path=None):
    global options

    def parse_and_set(path):
        for i, o in yaml.load(file(path)).iteritems():
            if i in options:
                options[i].set(o)
            else:
                define_option(i, o)

    parse_and_set(os.path.join(
        os.path.dirname(__file__), 'base_options.yaml'))
    if not path or not os.path.isfile(path):
        print """settings.yaml file does not exist,
                check if it has been copied from .dev or .product"""
    else:
        parse_and_set(path)

    # things to do after options parsed, seen as a preperation of main program
    # 1. set logger level
    logging.getLogger().setLevel(getattr(logging, options.logging.upper()))
    enable_pretty_logging()
