#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from torext.flask_style import FlaskStyleApp

app = FlaskStyleApp('demoapp')
app.settings.set('debug', True)

@app.route('get', '/')
def hello(hdr):
    hdr.write('ok')

logging.info(hello)
logging.info(hello.app)

@app.route('post', '/post')
def hello_post(self):
    print self.request.body
    self.write('ok post')

app.run()
