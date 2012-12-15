#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
from torext.utils import _json


class AllTestCase(unittest.TestCase):

    def setUp(self):
        from torext_project.app import app

        self.c = app.test_client()
        self.app = app

    def tearDown(self):
        self.c.close()

    def test_home_get(self):
        resp = self.c.get('/')
        settings_json = _json(self.app.settings)
        print resp.body
        print settings_json
        assert resp.body == settings_json

    def test_home_post(self):
        resp = self.c.post('/')
        content = open(os.path.join(self.app.root_path, 'app.py'), 'r').read()
        print resp.body
        print content
        assert resp.body == content

    def test_account(self):
        resp = self.c.get('/account')
        print resp.body
        assert resp.code == 200

        resp = self.c.get('/account/')
        print resp.body
        assert resp.code == 200

    def test_account_a(self):
        resp = self.c.get('/account/a')
        print resp.body
        assert resp.code == 200
