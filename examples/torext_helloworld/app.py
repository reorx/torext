#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.app import TorextApp
from torext.handlers import BaseHandler


app = TorextApp()


@app.route('/')
class HomeHandler(BaseHandler):
    def get(self):
        self.write('Hello World!')


if __name__ == '__main__':
    app.run()
