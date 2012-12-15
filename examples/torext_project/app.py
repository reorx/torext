#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp

import settings


app = TorextApp(settings, {
    'TEMPLATE_PATH': 'template',
    'STATIC_PATH': 'static',
})
app.setup()


app.route_many([
    ('', 'views'),
    ('/account', 'account.views')
])

print app.host_handlers


if __name__ == '__main__':

    app.command_line_config()
    app.run()
