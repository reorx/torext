#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
import settings


app = TorextApp(settings)


if '__main__' == __name__:
    app.command_line_config()
    app.run()
