#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import flask
from flask.ext import sqlalchemy


class BasicAppTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.config['SQLALCHEMY_ENGINE'] = 'mysql://reorx:mx320lf2@localhost/test_sa'
        app.config['TESTING'] = True
        db = sqlalchemy.SQLAlchemy(app)

        class User(db.Model):
            __tablename__ = 'user'
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
