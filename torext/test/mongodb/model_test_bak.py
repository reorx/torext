#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# To test:
#   - Document define
#   - .new()  # include consistency and inner operations
#   - .find()
#   - .exist()
#   - .one()
#   - .by__id()
#   - .by__id_str()
#
#   - .save()
#   - .copy()
#   - .remove()

import logging
from torext.testing import _TestCase


def random_str(length):
    import string
    from random import choice
    s = ''.join([choice(string.letters) for i in range(length)])
    return s


class TestModel(_TestCase):

    def setUp(self):
        from torext.conns import conns, configure_conns
        from torext.mongodb.model import Document, Struct, ObjectId

        # configure test logger
        test_logger = logging.getLogger('test')
        test_logger.propagate = 1

        SETTINGS = {
            'mongodb': {
                'core': {
                    'enable': True,
                    'username': 'None',
                    'password': 'None',
                    'host': '127.0.0.1',
                    'database': 'test',
                    'port': 27017
                }
            }
        }
        configure_conns(SETTINGS)
        mdb = conns.get('mongodb', 'core')
        self.assertTrue(mdb)

        class TestDoc(Document):
            col = mdb['test']['col0']
            struct = Struct({
                'id': ObjectId,
                'name': str,
                'age': int,
                'friends': [
                    {
                        'nick': str
                    }
                ]
            })

        self.Model = TestDoc

    def test_new(self):
        default = {
            # 'name': 'zorro',
            'age': 20,
            'friends': [
                self.Model.gen.friends({'nick': 'zorro'}),
                self.Model.gen.friends({'nick': 'webber'})
            ]
        }
        doc = self.Model.new(default=default)

        self.log.quiet(doc)
        self.log.quiet(default)

        for i in self.Model.struct:
            self.assertTrue(i in doc)

        # consistency
        self.assertEqual(doc['name'], '')
        self.assertEqual(doc['age'], default['age'])
        self.assertEqual(doc['friends'][0]['nick'], default['friends'][0]['nick'])

        # inner operations
        got_name = doc.inner_get('age')
        self.assertEqual(got_name, default['age'])
        got_friend_nick = doc.inner_get('friends.[1].nick')
        self.assertEqual(got_friend_nick,
                            default['friends'][1]['nick'])

        doc.inner_set('friends.[1].nick', 'tk')
        self.assertEqual(doc.inner_get('friends.[1].nick'), 'tk')

        doc.inner_del('friends.[0].nick')
        self.assertTrue('nick' not in doc.inner_get('friends.[0]'))

        doc.inner_del('friends.[0]')
        self.assertTrue(len(doc.inner_get('friends')) is 1)

    def test_save_and_find(self):
        name = random_str(10)

        doc_0 = self.Model.new(default={
            'name': name,
            'age': 0
        })
        doc_0.save()
        self.assertTrue(self.Model.find(doc_0.identifier).count() is 1)

        doc_1 = self.Model.new(default={
            'name': name,
            'age': 1
        })
        doc_1.save()
        self.assertTrue(self.Model.find(doc_1.identifier).count() is 1)

        cur = self.Model.find({'name': name})
        self.assertTrue(cur.count() >= 2)

        for i in cur:
            self.log.quiet('i age %s' % i['age'])
            self.assertTrue(i['age'] in (0, 1))

    def test_exist(self):
        from bson.objectid import ObjectId
        _id = ObjectId()

        self.assertFalse(self.Model.exist({'_id': _id}))

        doc = self.Model.new()
        doc.save()
        self.assertTrue(self.Model.exist({'_id': doc['_id']}))

    def test_one(self):
        from torext.errors import ObjectNotFound, MultiObjectsReturned
        nick = random_str(10)
        friends = [
            {
                'nick': nick
            }
        ]

        doc = self.Model.new({
            'friends': friends
        })
        self.assertRaises(ObjectNotFound, self.Model.one, doc.identifier)

        doc.save()
        self.assertEqual(doc, self.Model.one(doc.identifier))

        doc_dup = self.Model.new({
            'friends': friends
        })
        doc_dup.save()

        self.assertRaises(MultiObjectsReturned, self.Model.one, {'friends': friends})

    def test_by__id_and_by__id_str(self):
        doc = self.Model.new()
        doc.save()

        self.assertEqual(doc, self.Model.by__id(doc['_id']))
        self.assertEqual(doc, self.Model.by__id_str(str(doc['_id'])))
