#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from torext import settings


class HandlersContainer(object):
    def handlers(self):
        return self._handlers


class Module(HandlersContainer):
    def __init__(self, svc_label):
        self.import_path = settings.package + '.' + svc_label
        self._handlers = []

        # try:
        module = __import__(self.import_path, fromlist=[settings.package])
        self._handlers = getattr(module, 'handlers')
        # except ImportError, e:
        #     print 'import path', self.import_path
        #     logging.error('error when get handlers in module: ' + str(e))
        # except AttributeError, e:
        #     logging.error('error when get handlers in module: ' + str(e))


# TODO considering: if Router can be recursed by Router,
# so that it may be easier to invoke sub apps
class Router(HandlersContainer):
    def __init__(self, map):
        self.map = map
        self._handlers = []
        self._get_handlers()

    def _get_handlers(self):
        for path, mapper in self.map:
            if isinstance(mapper, (Module, Router)):
                for subPath, handler in mapper.handlers():
                    url = r'%s%s' % (path, subPath)
                    self._handlers.append(
                            (format_pattern(url), handler)
                    )
            else:
                url = r'%s' % path
                self._handlers.append(
                        (format_pattern(url), mapper)
                )

    def handlers(self):
        # if settings.application['debug']:
        #     log = '-> Handlers\n[' + ', '.join(['"%s"' % i[0] for i in self._handlers]) + ']'
        #     logging.info(log)
        return self._handlers


def include(*args):
    return Module(*args)


def format_pattern(ptn):
    if ptn.endswith('/') and len(ptn) > 1:
        ptn = ptn[:-1]
    return ptn
