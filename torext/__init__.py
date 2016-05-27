#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.0'

from .make_settings import settings
from .utils import LocalProxy
from .app import TorextApp


current_app = LocalProxy(lambda: TorextApp.current_app)
