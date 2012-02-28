#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import Application as TornadoApplication
from torext import settings


class BaseApplication(TornadoApplication):
    def __init__(self):
        # TODO resort settings
        self.settings = dict(
            debug=settings.debug,
            logging=settings.logging,
            template_path=settings.web['template_path'],
            autoescape=None,
        )
        self._setup()
        if not hasattr(self, 'handlers') or not hasattr(self, 'settings'):
            raise NotImplementedError("handlers and settings must set as App's attributes")
        super(BaseApplication, self).__init__(self.handlers, **self.settings)

    def _setup(self):
        raise NotImplementedError("_setup() must be rewritten")
