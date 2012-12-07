#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from nose.tools import *
from torext.flask_sql import SQLAlchemy


class MysqlTestCase(unittest.TestCase):
    def setUp(self):
        db = SQLAlchemy()

        db.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://reorx:mx320lf2@localhost/test_sa'

        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(20))

        self.User = User

        db.create_all()

        self.db = db

    def tearDown(self):
        self.db.drop_all()

    def test_create(self):
        u = self.User(name='reorx')
        self.db.session.add(u)
        self.db.session.commit()

        us = self.User.query.all()
        assert len(us) == 1
