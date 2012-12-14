#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
import settings


app = TorextApp(settings)
app.setup()


if __name__ == '__main__':

    app.command_line_config()
    app.run()
