#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from nose.tools import *
from torext.mongodb import Document, Struct, ObjectId, StructDefineError
from torext.errors import ValidationError, ObjectNotFound, MultipleObjectsReturned
from pymongo import Connection


_FAKE_DATA = {
    'another_id': ObjectId(),
    'name': 'reorx',
    'age': 20,
    'is_choosen': True,
    'skills': [
        {
            'name': 'Break',
            'power': 9.0
        }
    ],
    'magic': {
        'spell': 12.3,
        'camp': 'Chaos'
    }
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
                'age': int,
                'is_choosen': bool,
                'skills': [
                    {
                        'name': str,
                        'power': float
                    }
                ],
                'magic': {
                    'spell': float,
                    'camp': str
                }
            })

        self.Model = User
        self.db = db

    def tearDown(self):
        self.db.drop_collection(self.Model.col)

    def get_fake(self):
        d = fake_data()
        self.Model(d).validate()
        return d

    def test_define_error(self):
        with self.assertRaises(StructDefineError):
            class User(Document):
                struct = Struct({
                    'another_id': ObjectId,
                    'name': str,
                    'age': int,
                    'is_choosen': bool,
                    'skills': [
                        {
                            'name': 'wtf',
                            'power': float
                        }
                    ],
                    'magic': {
                        'spell': float,
                        'camp': str
                    }
                })

    def test_new_and_gen(self):
        with self.assertRaises(ValidationError):
            self.Model.new(magic=self.Model.gen.magic(camp=1))

        u = self.Model.new(
            name='reorx',
            age=20,
            is_choosen=True,
            skills=[
                self.Model.gen.skills(name='Kill')
            ],
            magic=self.Model.gen.magic(camp='Chaos'),
            # an extra key
            extra=None
        )

        print set(u.keys()), set(self.Model.struct.keys())
        assert (set(u.keys()) ^ set(self.Model.struct.keys())) == set(['extra', '_id'])

        assert u['name'] == 'reorx'
        assert u['age'] == 20
        assert u['is_choosen'] is True
        assert u['skills'][0]['name'] == 'Kill'
        assert u['magic']['camp'] == 'Chaos'

    def test_save(self):
        u = self.Model.new(
            name='reorx',
            age=20,
            is_choosen=True,
            skills=[
                self.Model.gen.skills(name='Kill')
            ],
            magic=self.Model.gen.magic(camp='Chaos')
        )

        rv = u.save()
        assert isinstance(rv, ObjectId) and rv == u['_id']

    def test_remove(self):
        pass

    def test_find(self):
        d = self.get_fake()

        self.Model.col.insert(d)
        cur = self.Model.find({'name': 'reorx'})
        assert cur.count() == 1

        u = cur.next()
        assert isinstance(u, Document)
        assert dict(u) == d

    def test_find_many(self):
        user_names = ['shinji', 'asuka', 'ayanami']
        for name in user_names:
            d = self.get_fake()
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
        d = self.get_fake()

        self.Model.col.insert(d)

        assert self.Model.exist({'name': 'reorx'})

        assert not self.Model.exist({'name': 'zorro'})

    def test_one(self):
        d = self.get_fake()

        self.Model.col.insert(d)
        query = {'name': 'reorx'}
        self.Model.one(query)

        self.Model.col.insert(self.get_fake())
        with self.assertRaises(MultipleObjectsReturned):
            self.Model.one(query)

        with self.assertRaises(ObjectNotFound):
            self.Model.one({'age': 1})

    def test_by__id(self):
        d = self.get_fake()

        _id = self.Model.col.insert(d)
        u = self.Model.by__id(_id)
        assert u['_id'] == _id

    def test_by__id_str(self):
        d = self.get_fake()

        _id = self.Model.col.insert(d)
        u = self.Model.by__id_str(str(_id))
        assert u['_id'] == _id

    def test_identifier(self):
        u = self.Model.new()
        assert u.identifier == {'_id': u['_id']}

    def test_deepcopy(self):
        d = self.get_fake()

        _id_str = self.Model.col.insert(d)
        u = self.Model.one({'_id': ObjectId(_id_str)})

        d = u.deepcopy()
        d['magic']['camp'] = 'Order'
        assert d['magic']['camp'] != u['magic']['camp']

        d['skills'].append(1)
        assert len(d['skills']) != len(u['skills'])
