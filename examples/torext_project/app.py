#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp

import settings


app = TorextApp(settings, {
    'LOG_RESPONSE': True
})
app.setup()


app.route_many([
    ('', 'views'),
    ('/api', 'api.views')
])

print app.host_handlers


if __name__ == '__main__':

    app.command_line_config()
    app.run()
