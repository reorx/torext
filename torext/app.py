#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import Application as TornadoApplication
from torext import settings


class BaseApplication(TornadoApplication):
    """
    Two ways to implement an application::
        1. Redefine the class
        >>> class Application(BaseApplication):
        >>>     def _setup(self):
        >>>         self._handlers = some_handlers
        >>>
        >>> app = Application()

        2. Directly use BaseApplication
        >>> app = BaseApplication(some_handlers)

    NOTE if you redefine you own application class, the setup function
    `_setup` must at least set `_handlers`as applications'sattributes
    """
    def __init__(self, handlers=None):
        self.settings = {
            'debug': settings.debug,
            'logging': settings.logging,
        }
        if settings.has('template_path'):
            self.settings['template_path'] = settings.template_path

        if handlers:
            self._handlers = handlers
        if hasattr(self, '_setup'):
            self._setup()
        if not hasattr(self, '_handlers'):
            raise NotImplementedError("`_handlers` must be set as App's attributes")
        super(BaseApplication, self).__init__(self._handlers, **self.settings)
