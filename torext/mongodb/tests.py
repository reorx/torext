#!/usr/bin/python
# -*- coding: utf-8 -*-

from torext.lib.testing import _TestCase


class TestModel(_TestCase):

    def setUp(self):
        from torext.db.connections import connections
        from torext.db.mongodb.model import _CollectionDeclarer, Document, Struct, ObjectId

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
        connections.configure(SETTINGS)
        mdb = connections.get('mongodb', 'core')
        self.assertTrue(mdb)

        class CollectionDeclarer(_CollectionDeclarer):
            connection = mdb

        class TestDoc(Document):
            col = CollectionDeclarer('test', 'col0')
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
        doc = self.Model.new(default={
            'friends': [self.Model.gen.friends(default={'nick': 'uo'})]
        })
        for i in self.Model.struct:
            self.assertTrue(i in doc)
        self.assertTrue(len(doc['friends']) == 1)

    def test_save(self):
        doc = self.Model.new()
        doc.save()
        self.assertTrue(self.Model.find(doc.identifier).count() is 1)

        doc['name'] = 'inserted'
        doc.save()
        self.assertTrue(self.Model.find(doc.identifier).next()['name'] == 'inserted')

    def test_consistency(self):
        default = {
            'age': 20,
            'friends': [
                {'nick': 'zorro'},
                {'nick': 'webber'}
            ]
        }
        doc = self.Model.new(default=default)
        self.logger.info(doc)
        self.logger.info(default)

        self.assertEqual(doc['name'], '')
        self.assertEqual(doc['age'], default['age'])
        self.assertEqual(doc['friends'][0]['nick'], default['friends'][0]['nick'])

    def test_inner_operations(self):
        default = {
            'name': '抚剑扬眉',
            'age': 16,
            'friends': [
                {'nick': 'zorro'},
                {'nick': 'webber'}
            ]
        }
        doc = self.Model.new(default=default)
        self.logger.info(default)

        self.assertEqual(doc.inner_get('name'), default['name'])
        self.assertEqual(doc.inner_get('friends.[1].nick'),
                            default['friends'][1]['nick'])
        doc.inner_set('friends.[1].nick', 'tk')
        self.assertEqual(doc.inner_get('friends.[1].nick'), 'tk')
        doc.inner_del('friends.[0].nick')
        self.assertTrue('nick' not in doc.inner_get('friends.[0]'))
        doc.inner_del('friends.[0]')
        self.assertTrue(len(doc.inner_get('friends')) is 1)
