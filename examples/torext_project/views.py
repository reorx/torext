#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from torext_project.base import BaseHandler


class HomeHdr(BaseHandler):
    def get(self):
        self.json_write(self.app.settings)

    def post(self):
        self.file_write(
            os.path.join(self.app.root_path, 'app.py'))


handlers = [
    ('/', HomeHdr),
]
