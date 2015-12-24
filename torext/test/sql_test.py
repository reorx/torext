#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sqlalchemy
except ImportError:
    print 'sqlalchemy is not installed, skip testing'
    from nose.plugins.skip import SkipTest
    raise SkipTest

try:
    with open('.mysqluri', 'r') as f:
        MYSQL_URI = f.read().strip()
except IOError:
    print 'mysql is not configured, skip sql_test'
    from nose.plugins.skip import SkipTest
    raise SkipTest

from nose.tools import assert_raises
from torext.app import TorextApp
from torext.sql import SQLAlchemy
from torext import errors


class TestSQLModule(object):
    def setup(self):
        app = TorextApp()
        app.settings['DEBUG'] = False
        app.settings['SQLALCHEMY'] = {
            'uri': MYSQL_URI,
            'echo': True
        }
        app.setup()

        self.create_database()

        db = SQLAlchemy(app=app)

        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(20))

        class Hub(db.Model):
            id = db.Column(db.Integer, primary_key=True)

        self.User = User
        self.Hub = Hub

        db.create_all()

        self.app = app
        self.db = db

    def teardown(self):
        # clean possible opened transactions
        self.db.session.commit()

        self.drop_database()

    def create_database(self):
        splited = MYSQL_URI.split('/')
        self.database_name = splited[-1]
        no_db_uri = '/'.join(splited[:-1])
        self.no_db_engine = sqlalchemy.create_engine(no_db_uri)
        self.no_db_engine.execute('create database if not exists %s;' % self.database_name)

    def drop_database(self):
        self.no_db_engine.execute('drop database %s;' % self.database_name)

    def test_create_delete(self):
        u = self.User(name='reorx')
        self.db.session.add(u)
        self.db.session.commit()

        us = self.User.query.all()
        assert len(us) == 1

        self.db.session.delete(u)

        us = self.User.query.all()
        assert len(us) == 0

    def test_get_or_raise(self):
        u = self.User(name='reorx')
        self.db.session.add(u)
        self.db.session.commit()

        assert self.User.query.get_or_raise(1).name == 'reorx'

        print 'DoesNotExist class', self.User.DoesNotExist
        with assert_raises(self.User.DoesNotExist):
            self.User.query.get_or_raise(2)

    def test_one_or_raise(self):
        u = self.User(name='reorx')
        self.db.session.add(u)

        u1 = self.User(name='reorx')
        self.db.session.add(u1)

        self.db.session.commit()

        assert self.User.query.filter(self.User.id == 2).one_or_raise().name == 'reorx'

        with assert_raises(self.User.DoesNotExist):
            try:
                self.User.query.filter(self.User.name == 'others').one_or_raise()
            except self.Hub.DoesNotExist:
                pass

        with assert_raises(errors.MultipleObjectsReturned):
            self.User.query.filter(self.User.name == 'reorx').one_or_raise()
