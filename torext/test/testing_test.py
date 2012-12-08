#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import unittest
from torext.app import TorextApp
from torext.handlers import _BaseHandler


GET_RESULT = 'get ok'
POST_RESULT = 'post ok'


def make_app():
    app = TorextApp()

    @app.route('/')
    class TestHdr(_BaseHandler):
        def get(self):
            return self.write(GET_RESULT)

        def post(self):
            return self.write(POST_RESULT)

    app.update_settings({
        'TESTING': True
    })
    return app


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        app = make_app()

        self.c = app.test_client()

    def test_get(self):
        # TODO with params
        rv = self.c.get('/')
        logging.info(' logging info ')
        rl = logging.getLogger()
        print rl.handlers
        print repr(rv.body)
        assert rv.body == GET_RESULT

    def test_post(self):
        # TODO with data
        rv = self.c.post('/')
        print repr(rv.body)
        assert rv.body == POST_RESULT

    def test_header_change(self):
        pass

# TODO multiple TestCase
