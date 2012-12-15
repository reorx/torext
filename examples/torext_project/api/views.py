#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from torext_project.base import BaseHandler
from tornado.web import HTTPError


class ApiHandler(BaseHandler):
    EXCEPTION_HANDLERS = {
        HTTPError: '_handle_http_error'
    }

    def _handle_http_error(self, e):
        self.json_error(e.status_code, e)

    def json_error(self, code, error=None):
        msg = {'code': code}
        if isinstance(error, Exception):
            msg['error'] = str(error)
            logging.info('Get error to write: %s - %s' %
                         (error.__class__.__name__, error))
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.set_status(code)
        self.json_write(msg, code=code)


class SourceHandler(ApiHandler):
    def get(self, name):
        path = os.path.join(self.app.root_path, name)
        if not os.path.exists(path) or os.path.isdir(path):
            raise HTTPError(404, 'File not found')

        with open(path, 'r') as f:
            source = f.read()

        try:
            source.decode('utf8')
        except Exception, e:
            raise HTTPError(403, 'Not a valid utf-8 text file, %s' % e)

        d = {
            'name': name,
            'source': source
        }
        self.json_write(d)


class SettingsHandler(ApiHandler):
    def get(self):
        self.json_write(self.app.settings)


handlers = [
    ('/source/(.*)', SourceHandler),
    ('/settings.json', SettingsHandler),
]
