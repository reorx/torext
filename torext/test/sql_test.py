#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlalchemy
except ImportError:
    print 'sqlalchemy is not installed, skip testing'
    from nose.plugins.skip import SkipTest
    raise SkipTest

import unittest
from torext.app import TorextApp
from torext.sql import SQLAlchemy


class MysqlTestCase(unittest.TestCase):
    def setUp(self):
        app = TorextApp()
        app.settings['DEBUG'] = False
        app.settings['SQLALCHEMY'] = {
            'uri': 'mysql://root:zxsaqw21@localhost/torext_test',
            'echo': True
        }
        app.setup()
        db = SQLAlchemy(app=app)

        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(20))

        self.User = User

        db.create_all()

        self.app = app
        self.db = db

    def tearDown(self):
        # clean possible opened transactions
        self.db.session.commit()

        self.db.drop_all()

    def test_create_delete(self):
        u = self.User(name='reorx')
        self.db.session.add(u)
        self.db.session.commit()

        us = self.User.query.all()
        assert len(us) == 1

        self.db.session.delete(u)

        us = self.User.query.all()
        assert len(us) == 0


if __name__ == '__main__':
    unittest.main()
