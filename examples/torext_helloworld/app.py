#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
from torext.handlers import _BaseHandler


app = TorextApp()


@app.route('/')
class HomeHandler(_BaseHandler):
    def get(self):
        self.write('Hello World!')


if __name__ == '__main__':
    app.run()
