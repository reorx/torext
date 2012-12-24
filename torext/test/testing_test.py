#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from torext.app import TorextApp
from torext.handlers import BaseHandler
from torext.testing import AppTestCase


GET_RESULT = 'get ok'
POST_RESULT = 'post ok'


def make_app():
    app = TorextApp()

    @app.route('/')
    class HomeHdr(BaseHandler):
        def get(self):
            self.write(GET_RESULT)

        def post(self):
            self.write(POST_RESULT)

    @app.route('/withdata')
    class WithdataHdr(BaseHandler):
        def get(self):
            self.write(self.get_argument('p'))

        def post(self):
            self.write(self.get_argument('d'))

    @app.route('/header')
    class HeaderHdr(BaseHandler):
        def get(self):
            header_name = self.get_argument('h')
            header_value = self.request.headers.get(header_name)
            self.set_header(header_name, header_value)
            self.write(header_value)

    # although this is not needed, it's good to be set explicitly
    app.update_settings({
        'TESTING': True
    })
    return app


class CaseMixin(object):
    def test_get(self):
        rv = self.c.get('/')
        assert rv.body == GET_RESULT

    def test_post(self):
        rv = self.c.post('/')
        assert rv.body == POST_RESULT

    def test_get_params(self):
        p = 'fly me to the moon'
        rv = self.c.get('/withdata', {'p': p})
        assert rv.body == p

    def test_post_data(self):
        d = 'in other words'
        rv = self.c.post('/withdata', {'d': d})
        assert rv.body == d

    def test_header_change(self):
        h = 'darling kiss me'
        name = 'Torext-Special'
        rv = self.c.get('/header', {'h': name}, headers={name: h})

        assert rv.headers.get(name) == h
        assert rv.body == h


class BasicTestCase(unittest.TestCase, CaseMixin):
    def setUp(self):
        app = make_app()

        self.c = app.test_client()

    def tearDown(self):
        self.c.close()


class AppTestCaseTest(AppTestCase, CaseMixin):
    def get_client(self):
        return make_app().test_client()


app = make_app()


class AppGeneratedTestCaseTest(app.TestCase, CaseMixin):
    pass
