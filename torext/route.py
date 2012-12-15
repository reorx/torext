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
        try:
            module = __import__(self.import_path, fromlist=[settings['PROJECT']])
        except ImportError, e:
            raise URLRouteError('Caught ImportError when router was searching modules: %s' % e)

        try:
            self._handlers = getattr(module, 'handlers')
        except AttributeError, e:
            raise URLRouteError('Caught error when router was getting handlers from module: %s' % e)

        logging.debug('got handlers from module %s' % self.import_path)

        for i in self._handlers:
            if isinstance(i[1], ModuleSearcher):
                raise URLRouteError('You should not use `include` in subapp handlers')

        return self._handlers


class Router(object):
    def __init__(self, rules):
        self.rules = rules
        self._handlers = []

    def get_handlers(self):
        for path, rule_or_hdr in self.rules:
            if isinstance(rule_or_hdr, str):
                searcher = ModuleSearcher(rule_or_hdr)
                for sub_path, hdr in searcher.get_handlers():
                    self.add('%s%s' % (path, sub_path), hdr)
            else:
                self.add('%s' % path, rule_or_hdr)

        return self._handlers

    def add(self, url, hdr):
        logging.debug('add url-hdr in router: (%s, %s)' % (url, hdr))
        self._handlers.append(
            (url, hdr)
        )


def include(label):
    return ModuleSearcher(label)


def format_pattern(ptn):
    if ptn.endswith('/') and len(ptn) > 1:
        ptn = ptn[:-1]
    return ptn
