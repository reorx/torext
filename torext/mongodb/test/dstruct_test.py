#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# To test:
#   - validate_dict
#   - build_dict
#   - index_dict
#   - map_dict
#   - hash_dict
#   - Struct
#
#   - class define (in setUp)
#   - build_instance
#   - validate
#   - inner operations (inner_get, set, del)

import logging
from functools import partial

from torext.mongodb.dstruct import (
    ValidationError,
    validate_dict,
    build_dict,
    index_dict,
    map_dict,
    hash_dict,
    StructuredDict,
    Struct,
    ObjectId)

from torext.testing import _TestCase


class TestFunctions(_TestCase):
    def setUp(self):
        # configure test logger
        test_logger = logging.getLogger('test')
        test_logger.propagate = 1
        test_logger.setLevel(logging.DEBUG)

        self.doc = {
            'str_id': None,
            'name': 'reorx',
            'nature': {'luck': 10},
            'people': ['aoyi'],
            'disks': [
                {
                    'title': 'My Passport',
                    'volums': [
                        {
                            'size': 1,
                            'block': [12, 4, 32]
                        }
                    ]
                },
                {
                    'title': 'DATA',
                    'volums': [
                        {
                            'size': 2,
                            'block': [1, 2, 3]
                        }
                    ]
                }
            ],
            'extra': 'oos'
        }

    def test_validate_dict(self):
        func = partial(validate_dict,
            allow_None_types=[str],
            brother_types=[
                (str, unicode),
                (int, long),
            ])

        def assertValidationError(fn, *args, **kwgs):
            try:
                fn(*args, **kwgs)
            except ValidationError:
                pass
            else:
                raise Exception('%s args:%s kwgs:%s should raise error' % (fn.func, args, kwgs))

        structure_r = {
            'str_id': str,
            'name': str,
            'nature': {
                'luck': int,
            },
            'people': [str],
            'disks': [
                {
                    'title': str,
                    'volums': [
                        {
                            'size': int,
                            'block': [int]
                        }
                    ]
                }
            ],
            'extra': str
        }
        func(self.doc, structure_r)

        # missing 'people' and 'extra' and 'title' in 'disks'
        structure_w_missing_key = {
            'str_id': str,
            'name': str,
            'nature': {
                'luck': int,
            },
            'disks': [
                {
                    'volums': [
                        {
                            'size': int,
                            'block': [int]
                        }
                    ]
                }
            ],
        }
        func(self.doc, structure_w_missing_key)

        structure_w_diff_key = {
            'str_id': str,
            'nimei': str,
            'nature': {
                'lust': int,
            },
            'people': [str],
            'disks': [
                {
                    'title': str,
                    'volums': [
                        {
                            'size': int,
                            'block': [int]
                        }
                    ]
                }
            ],
            'extra': str
        }
        assertValidationError(func, self.doc, structure_w_diff_key)

        structure_w_diff_type = {
            'str_id': str,
            'name': str,
            'nature': {
                'luke': int,
            },
            'people': [str],
            'disks': [
                {
                    'title': str,
                    'volums': [
                        {
                            'size': str,
                            'block': [int]
                        }
                    ]
                }
            ],
            'extra': str
        }
        assertValidationError(func, self.doc, structure_w_diff_type)

    def test_build_dict(self):
        structure = {
            'str_id': str,
            'name': str,
            'nature': {
                'luck': int,
            },
            'people': [str],
            'disks': [
                {
                    'title': str,
                    'volums': [
                        {
                            'size': int,
                            'block': [int]
                        }
                    ]
                }
            ],
            'extra': str
        }
        doc_plain = build_dict(structure)
        self.log.quiet(str(doc_plain))
        validate_dict(doc_plain, structure)

        doc_with_default = build_dict(structure, default={
            'name': 'hello',
            'nature.luck': 3
        })
        self.log.quiet(str(doc_with_default))
        validate_dict(doc_with_default, structure)

    def test_index_dict(self):
        self.assertEqual(self.doc['name'], index_dict(self.doc, 'name'))
        self.assertEqual(self.doc['people'][0], index_dict(self.doc, 'people.[0]'))
        self.assertEqual(self.doc['nature']['luck'], index_dict(self.doc, 'nature.luck'))
        self.assertEqual(self.doc['disks'][0]['volums'][0]['size'], index_dict(self.doc, 'disks.[0].volums.[0].size'))

    def test_map_dict(self):
        doc_map = map_dict(self.doc)
        self.log.quiet(doc_map)
        self.assertTrue('name' in doc_map)
        self.assertTrue('people.[0]' in doc_map)
        self.assertTrue('disks.[0].volums.[0].size' in doc_map)

    def test_hash_dict(self):
        self.assertEqual(hash_dict(self.doc), hash_dict(self.doc))


class TestStruct(_TestCase):
    def setUp(self):
        class SomeStruct(StructuredDict):
            struct = Struct({
                'str_id': str,
                'name': str,
                'nature': {
                    'luck': int,
                },
                'people': [str],
                'disks': [
                    {
                        'title': str,
                        'volums': [
                            {
                                'size': int,
                                'block': [int]
                            }
                        ]
                    }
                ],
                'extra': str
            })

            allow_None_types = [str, unicode, ]

            brother_types = [
                (str, unicode),
                (int, long),
            ]

        self.SDict = SomeStruct

    def test_all(self):
        # test build_instance and validate (done in build_instance)
        ins = self.SDict.build_instance({
            'name': 'star',
            'disks': [
                self.SDict.gen.disks(default={
                    'title': 'woooo',
                    'volums': [
                        self.SDict.gen.disks.volums(default={
                            'size': 100000,
                            'block': [1, 3, 5, 7]
                        })
                    ]
                })
            ]
        })
        self.log.quiet(ins)

        # test if keys in ins
        self.assertTrue(len(ins['disks']) == 1)
        self.assertEqual(ins['disks'][0]['title'], 'woooo')
        self.assertTrue(len(ins['disks'][0]['volums']) == 1)

        # test inner operations
        ins.inner_set('disks.[0].title', 'tk')
        self.assertEqual(ins.inner_get('disks.[0].title'), 'tk')
        ins.inner_del('disks.[0].title')
        self.assertTrue('title' not in ins.inner_get('disks.[0]'))
        ins.inner_del('disks.[0]')
        self.assertTrue(len(ins.inner_get('disks')) is 0)
