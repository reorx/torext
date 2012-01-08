#!/usr/bin/python
# -*- coding: utf-8 -*-

import yaml
import os.path
import logging
from tornado.options import (options,
                             enable_pretty_logging,
                             define)


def initialize(options_file_path):
    # setp 1. set options
    parse_and_set(os.path.join(
        os.path.dirname(__file__), 'fixtures/base_options.yaml'))
    if not options_file_path or not os.path.isfile(options_file_path):
        print """settings.yaml file does not exist,
                 check if it has been copied from .dev or .product"""
    else:
        parse_and_set(options_file_path)

    # setp 2. set logging
    logging.getLogger().setLevel(getattr(logging, options.logging.upper()))
    enable_pretty_logging()


def parse_and_set(path):
    global options
    for i, o in yaml.load(file(path)).iteritems():
        if i in options:
            options[i].set(o)
        else:
            define(i, o)
