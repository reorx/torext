#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging

_abspath = lambda x: os.path.abspath(x)
_join = lambda x, y: os.path.join(x, y)
_abs_join = lambda x, y: _abspath(_join(x, y))

def parse_options(path):
    import yaml
    from tornado.options import options
    from tornado.options import define as define_option

    def parse_and_set(path):
        for i, o in yaml.load(file(path)).iteritems():
            if i in options:
                options[i].set(o)
            else:
                define_option(i, o)

    parse_and_set(os.path.join(
        os.path.dirname(__file__), 'base_options.yaml'))
    if not os.path.isfile(path):
        logging.warning("""settings.yaml file does not exist,
                check if it has been copied from .dev or .product""")
    else:
        parse_and_set(path)
