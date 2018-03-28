#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#import unittest
import tempfile
try:
    import simplejson as json
except ImportError:
    import json

from torext.app import TorextApp
from torext.handlers.base import BaseHandler
from torext import errors
from torext.utils import generate_cookie_secret
from torext.compat import str_
from nose.tools import eq_


EXC_MSG_0 = 'not pass'
EXC_MSG_1 = 'invalid'
EXC_MSG_2 = 'need proper index'

JSON_DICT = {'eva': 'evangelion'}

FILE_CONTENT = """
Mari Illustrious Makinami
Voiced by: Maaya Sakamoto (Japanese), Trina Nishimura (English)
"""

SIGNED_NAME = 'EVA-02'
SIGNED_RAW_VALUE = 'Asuka Langley Soryu'

BUF_DICT = {
    '01': 'You Are (Not) Alone',
    '02': 'You Can (Not) Advance',
    '03': 'You Can (Not) Redo'
}


class AuthenticationNotPass(errors.TorextException):
    pass


class ValidationError(errors.TorextException):
    pass


def same_dict(d1, d2):
    return set(d1.keys()) == set(d2.keys()) and\
        not [i for i in d1 if d1[i] != d2[i]]


app = TorextApp()
app.settings['COOKIE_SECRET'] = generate_cookie_secret()


@app.route('/')
class HomeHandler(BaseHandler):
    EXCEPTION_HANDLERS = {
        AuthenticationNotPass: '_handle_401',
        (ValidationError, IndexError): '_handle_400'
    }

    def get(self):
        exc = int(self.get_argument('exc'))
        if exc == 0:
            raise AuthenticationNotPass(EXC_MSG_0)
        elif exc == 1:
            raise ValidationError(EXC_MSG_1)
        elif exc == 2:
            raise IndexError(EXC_MSG_2)

    def _handle_401(self, e):
        # unauthorized
        self.set_status(401)
        self.write(str(e))

    def _handle_400(self, e):
        # bad request
        self.set_status(400)
        self.write(str(e))


@app.route('/file')
class FileHandler(BaseHandler):
    def get(self):
        _, fname = tempfile.mkstemp()
        with open(fname, 'w') as f:
            f.write(FILE_CONTENT)

        self.write_file(fname, mime_type='text/plain')
        os.remove(fname)


@app.route('/cookie')
class CookieHandler(BaseHandler):
    def get(self):
        signed_value = self.create_signed_value(SIGNED_NAME, SIGNED_RAW_VALUE)
        self.set_cookie(SIGNED_NAME, signed_value)

    def post(self):
        print('request header', self.request.headers)
        print('request cookies', self.request.cookies)
        cookie_value = self.get_cookie(SIGNED_NAME)
        self.write(self.decode_signed_value(SIGNED_NAME, cookie_value))


@app.route('/prepare')
class PrepareHandler(BaseHandler):
    PREPARES = ['01', '02', '03']

    def get(self):
        self.write_json(self.prepare_buf)

    def prepare_01(self):
        self.prepare_buf = {}
        self.prepare_buf['01'] = BUF_DICT['01']

    def prepare_02(self):
        self.prepare_buf['02'] = BUF_DICT['02']

    def prepare_03(self):
        self.prepare_buf['03'] = BUF_DICT['03']


@app.route('/json')
class JsonHandler(BaseHandler):
    def get(self):
        if self.get_argument('write_json', None):
            self.write_json(JSON_DICT, code=201, headers={'EVA-01': 'Shinji Ikari'})
        else:
            self.write(self.json_encode(JSON_DICT))

    def post(self):
        print('headers', self.request.headers)
        data = self.get_argument('data')
        d = self.json_decode(data)
        if d == JSON_DICT:
            self.set_status(200)
        else:
            self.set_status(400)


class BaseHandlerRequestTest(app.TestCase):
    def test_handle_request_exception(self):
        resp = self.c.get('/', {'exc': 0})
        eq_(resp.code, 401)
        eq_(str_(resp.body), EXC_MSG_0)

        resp = self.c.get('/', {'exc': 1})
        eq_(resp.code, 400)
        eq_(str_(resp.body), EXC_MSG_1)

        resp = self.c.get('/', {'exc': 2})
        eq_(resp.code, 400)
        eq_(str_(resp.body), EXC_MSG_2)

    def test_file_write(self):
        resp = self.c.get('/file')
        print(repr(resp.body))
        eq_(str_(resp.body), FILE_CONTENT)

        eq_(resp.headers.get('Content-Type'), 'text/plain')
        assert 'Last-Modified' in resp.headers
        assert 'ETag' in resp.headers

    def test_decode_signed_value(self):
        resp = self.c.get('/cookie')
        print(resp.cookies)
        resp_post = self.c.post('/cookie', cookies=resp.cookies)
        print(repr(resp_post.body))
        eq_(str_(resp_post.body), SIGNED_RAW_VALUE)

    def test_prepare(self):
        resp = self.c.get('/prepare')
        eq_(json.loads(resp.body), BUF_DICT)

    def test_json_write(self):
        resp = self.c.get('/json?write_json=1')
        eq_(resp.code, 201)
        eq_(resp.headers.get('EVA-01'), 'Shinji Ikari')

        eq_(json.loads(resp.body), JSON_DICT)

    def test_dump_dict(self):
        resp = self.c.get('/json')
        print(resp.body)
        eq_(json.loads(resp.body), JSON_DICT)

    def test_parse_json(self):
        resp = self.c.post('/json', data={'data': json.dumps(JSON_DICT)})
        eq_(resp.code, 200)
