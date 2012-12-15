#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
from torext.utils import _json, _dict


class AllTestCase(unittest.TestCase):

    def setUp(self):
        from torext_project.app import app

        self.c = app.test_client()
        self.app = app

    def tearDown(self):
        self.c.close()

    def test_home_get(self):
        resp = self.c.get('/')
        assert resp.code == 200

    def test_home_post(self):
        resp = self.c.post('/')
        assert resp.code == 405

    def test_api_settings(self):
        resp = self.c.get('/api/settings.json')
        settings_json = _json(self.app.settings)
        print resp.body, settings_json
        assert resp.body == settings_json

    def test_api_source(self):
        resp = self.c.get('/api/source/app.py')
        content = open(os.path.join(self.app.root_path, 'app.py'), 'r').read()
        d = _dict(resp.body)
        print d
        assert d['source'] == content
