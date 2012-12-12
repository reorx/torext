#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from nose.tools import *
from torext.mongodb import Document, Struct, ObjectId
from pymongo import Connection


def include_dict(d1, d2):
    """d1 include d2
    """
    s1 = set(d1.keys())
    s2 = set(d2.keys())
    return (s1 & s2) == s2 and not [i for i in d2 if d2[i] != d1[i]]


_FAKE_DATA = {
    'name': 'reorx',
    'age': 20
}

fake_data = lambda: _FAKE_DATA.copy()


class ModelTest(unittest.TestCase):

    def setUp(self):
        db = Connection('mongodb://localhost')['torext']

        class User(Document):
            col = db['user']
            struct = Struct({
                'another_id': ObjectId,
                'name': str,
                'age': int
            })

        self.Model = User
        self.db = db

    def tearDown(self):
        self.db.connection.drop_database(self.db.name)

    def test_new(self):
        u = self.Model.new(fake_data())
        print dict(u)
        assert include_dict(dict(u), fake_data())

    def test_save(self):
        u = self.Model.new(fake_data())
        rv = u.save()
        print rv
        assert rv

    def test_remove(self):
        pass

    def test_find(self):
        self.Model.col.insert(fake_data())
        cur = self.Model.find({'name': 'reorx'})
        assert cur.count() == 1
        u = cur.next()
        assert isinstance(u, Document)
        assert include_dict(dict(u), fake_data())

    def test_find_many(self):
        user_names = ['shinji', 'asuka', 'ayanami']
        for name in user_names:
            d = fake_data().copy()
            d['name'] = name
            d['age'] = 14
            print d
            self.Model.col.insert(d)
        cur = self.Model.find({'age': 14})
        print [i for i in cur]
        assert cur.count() == 3
        for u in cur:
            assert isinstance(u, Document)
            assert u['name'] in user_names

    def test_exist(self):
        pass

    def test_one(self):
        pass

    def test_by__id(self):
        pass

    def test_by__id_str(self):
        pass

    def test_identifier(self):
        pass

    def test_copy(self):
        d = fake_data()
        d['inner'] = {
            'pers': 1
        }
        _id_str = self.Model.col.insert(d)
        u = self.Model.one({'_id': ObjectId(_id_str)})
        print u
        ud = dict(u)
        ud['inner']['ins'] = 1
        print ud
        assert 0
        pass
