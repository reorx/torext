#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from torext.lep_sql import SQLAlchemy


class MysqlTestCase(unittest.TestCase):
    def setUp(self):
        db = SQLAlchemy('mysql://reorx:mx320lf2@localhost/test_sa', pool_recycle=3600)

        from sqlalchemy import Column, String, Integer

        class User(db.Model):
            __tablename__ = 'user'
            id = Column(Integer, primary_key=True)
            name = Column(String(20))

        self.User = User

        db.create_db()

        self.db = db

    def tearDown(self):
        self.User.metadata.drop_all(self.db.engine)

    def test_create(self):
        u = self.User(name='reorx')
        self.db.session.add(u)
        self.db.session.commit()

        us = self.User.query.all()
        assert len(us) == 1
