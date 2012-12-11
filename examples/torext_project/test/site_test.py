#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest


class AllTestCase(unittest.TestCase):

    def setUp(self):
        from tortest.app import app

        self.c = app.test_client()

    def test_home(self):
        resp = self.c.get('/')
        assert resp.body == 'get ok'

    def test_account_a(self):
        resp = self.c.get('/account/a')
        assert resp.body == '/account/a'
