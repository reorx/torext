#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.flask_style import FlaskStyleApp


app = FlaskStyleApp('appname')


@app.route('get', '/')
def hello(hdr):
    hdr.write('ok')


@app.route('post', '/user/profile')
def hello_post(hdr):
    hdr.write('ok post')


if __name__ == '__main__':
    app.run()
