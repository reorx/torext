#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from torext import settings
from torext.errors import URLRouteError


class ModuleSearcher(object):
    def __init__(self, label):
        assert settings['PROJECT'], 'you must set PROJECT first'
        self.import_path = settings['PROJECT'] + '.' + label
        self._handlers = []

    def get_handlers(self):
        module = __import__(self.import_path, fromlist=[settings['PROJECT']])

        try:
            self._handlers = getattr(module, 'handlers')
        except AttributeError, e:
            # TODO enhanced traceback
            raise URLRouteError('Caught error when router was getting handlers from module: %s' % e)

        logging.debug('got handlers from module %s' % self.import_path)

        for i in self._handlers:
            if isinstance(i[1], ModuleSearcher):
                raise URLRouteError('You should not use `include` in subapp handlers')

        return self._handlers


class Router(object):
    def __init__(self, specs, prefix=None):
        self.specs = specs
        self.prefix = prefix
        self._handlers = []

    def get_handlers(self):
        for spec in self.specs:
            if isinstance(spec[1], str):
                searcher = ModuleSearcher(spec[1])
                for searcher_spec in searcher.get_handlers():
                    _searcher_spec = list(searcher_spec)
                    _searcher_spec[0] = spec[0] + _searcher_spec[0]
                    self.add(tuple(_searcher_spec))
            else:
                self.add(spec)

        return self._handlers

    def add(self, spec):
        if self.prefix:
            spec = (self.prefix + spec[0], spec[1])
        logging.debug('add url spec in router: %s' % str(spec))
        self._handlers.append(spec)


def include(label):
    return ModuleSearcher(label)


def format_pattern(ptn):
    if ptn.endswith('/') and len(ptn) > 1:
        ptn = ptn[:-1]
    return ptn
