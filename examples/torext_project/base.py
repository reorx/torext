#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from torext.handlers import _BaseHandler


class BaseHandler(_BaseHandler):
    def json_error(self, code, error=None):
        msg = {'code': code}
        if isinstance(error, Exception):
            # NOTE(maybe) if use __str__() it will cause UnicodeEncodeError when error contains Chinese unicode
            msg['error'] = str(error)
            logging.info('Get error to write: %s - %s' %
                         (error.__class__.__name__, error))
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.set_status(code)
        self.json_write(msg, code=code)
