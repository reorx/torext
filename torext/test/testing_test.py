#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from torext.app import TorextApp
from torext.handlers import _BaseHandler


GET_RESULT = 'get ok'
POST_RESULT = 'post ok'


def make_app():
    class TestHdr(_BaseHandler):
        def get(self):
            return self.write(GET_RESULT)

        def post(self):
            return self.write(POST_RESULT)

    app = TorextApp()
    app.update_settings({
        'TESTING': True
    })
    app.add_handler('/', TestHdr)


class TestCase(unittest.TestCase):
    def setUp(self):
        app = make_app()

        self.c = app.test_client()

    def test_get(self):
        rv = self.c.get('/')
        print repr(rv.body)
        assert rv.body == GET_RESULT

    def test_post(self):
        rv = self.c.post('/')
        print repr(rv.body)
        assert rv.body == POST_RESULT
