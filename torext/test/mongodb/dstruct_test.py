#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import datetime
import copy

from torext.mongodb.dstruct import (
    check_struct,
    build_dict,
    retrieve_dict,
    map_dict,
    hash_dict,
    StructuredDict,
    Struct,
    ObjectId,
    ValidationError,
    validate_dict,
    StructDefineError,
)


STRUCT_SAMPLE = {
    'id': ObjectId,
    'name': str,
    'nature': {
        'luck': int,
    },
    'people': [str],
    'disks': [
        {
            'is_primary': bool,
            'last_modified': datetime.datetime,
            'volums': [
                {
                    'name': str,
                    'size': int,
                    'block': [int]
                }
            ]
        }
    ],
    'extra': float
}


DICT_SAMPLE = {
    'id': ObjectId(),
    'name': 'reorx',
    'nature': {
        'luck': 1,
    },
    'people': ['ayanami', 'asuka'],
    'disks': [
        {
            'is_primary': True,
            'last_modified': datetime.datetime.now(),
            'volums': [
                {
                    'name': 'EVA-01',
                    'size': 1048,
                    'block': [1, 2, 3]
                }
            ]
        }
    ],
    'extra': float(1.234)
}


class UtilitiesTest(unittest.TestCase):
    def setUp(self):
        pass

    def s(self, **kwgs):
        d = copy.deepcopy(STRUCT_SAMPLE)
        d.update(kwgs)
        return d

    def d(self, **kwgs):
        d = copy.deepcopy(DICT_SAMPLE)
        d.update(kwgs)
        return d

    def test_check_struct(self):
        check_struct(self.s())
        with self.assertRaises(StructDefineError):
            check_struct(self.s(name='hello'))
        with self.assertRaises(StructDefineError):
            check_struct(self.s(people=['me']))
        with self.assertRaises(StructDefineError):
            d = self.s()
            d['nature']['luck'] = 9
            check_struct(d)
        with self.assertRaises(StructDefineError):
            d = self.s()
            d['disks'][0]['volums'][0]['block'][0] = 1024
            check_struct(d)
        with self.assertRaises(StructDefineError):
            d = self.s()
            d['disks'][0]['volums'][0]['name'] = 'C'
            check_struct(d)

    def test_validate_dict(self):
        d = self.d()

        # no more, no less
        validate_dict(d, self.s())

        # wrong type
        d = self.d(id=1)
        with self.assertRaises(ValidationError):
            validate_dict(d, self.s())

        # None
        d = self.d(name=None)
        with self.assertRaises(ValidationError):
            validate_dict(d, self.s())

    def test_validate_dict_more_less(self):
        d = self.d()

        # more
        extra_value = 'are you?'
        d['_d'] = extra_value
        d['nature']['_nature'] = extra_value
        d['disks'][0]['_disks'] = extra_value
        d['disks'][0]['volums'][0]['_volums'] = extra_value
        validate_dict(d, self.s())

        # less
        del d['disks'][0]['volums'][0]['size']
        with self.assertRaises(ValidationError):
            validate_dict(d, self.s())

    def test_validate_dict_allow_None_types(self):
        d = self.d(name=None)
        with self.assertRaises(ValidationError):
            validate_dict(d, self.s())

        validate_dict(d, self.s(), allow_None_types=[str])

    def test_validate_dict_brother_types(self):
        d = self.d()
        d['nature']['luck'] = float(3.14159)
        with self.assertRaises(ValidationError):
            validate_dict(d, self.s(), allow_None_types=[str])

        validate_dict(d, self.s(), allow_None_types=[str], brother_types=[(int, float)])

    # require validate_dict
    def test_build_dict(self):
        d1 = build_dict(self.s(), extra=1.11)
        print d1
        validate_dict(d1, self.s())

        d2 = build_dict(self.s())

        assert str(d1['id']) != str(d2['id'])

    def test_retrieve_dict(self):
        d = self.d()
        assert d['name'] == retrieve_dict(d, 'name')
        assert d['people'][1] == retrieve_dict(d, 'people.[1]')
        assert d['nature']['luck'] == retrieve_dict(d, 'nature.luck')
        assert d['disks'][0]['volums'][0]['size'] == retrieve_dict(d, 'disks.[0].volums.[0].size')

    # require test_retrieve_dict
    def test_map_dict(self):
        d = self.d()
        mapping = map_dict(d)
        for k, v in mapping.iteritems():
            assert retrieve_dict(d, k) == v

    def test_hash_dict(self):
        d1 = self.d()
        d2 = self.d()
        assert d1 is not d2
        assert hash_dict(d1) == hash_dict(d2)

        # change d2
        d2['id'] = ObjectId()
        assert hash_dict(d1) != hash_dict(d2)

        # acturally a test for validate_dict,
        # to test whether dict is changed or not after validate process
        d3 = self.d()
        hash_before = hash_dict(d3)
        validate_dict(d3, self.s())
        assert hash_dict(d3) == hash_before


class StructedDictTest(unittest.TestCase):
    def setUp(self):
        class UserDict(StructuredDict):
            struct = Struct({
                'id': ObjectId,
                'name': str,
                'nature': {
                    'luck': int,
                },
                'people': [str],
                'disks': [
                    {
                        'is_primary': bool,
                        'last_modified': datetime.datetime,
                        'volums': [
                            {
                                'name': str,
                                'size': int,
                                'block': [int]
                            }
                        ]
                    }
                ],
                'extra': float
            })

        self.S = UserDict

    # requires UtilitiesTest.test_validate_dict
    def test_validate(self):
        d = copy.deepcopy(DICT_SAMPLE)
        validate_dict(d, self.S.struct,
                      allow_None_types=self.S.allow_None_types,
                      brother_types=self.S.brother_types)

        sd = self.S(d)
        sd.validate()

    # internally requires test_validate
    def test_build_instance(self):
        ins = self.S.build_instance()
        d = build_dict(self.S.struct)
        del ins['id']
        del d['id']
        assert hash_dict(ins) == hash_dict(d)

        with self.assertRaises(ValidationError):
            ins = self.S.build_instance(name=1)

        ins = self.S.build_instance(
            name='reorx',
            nature={
                'luck': 10
            }
        )
        assert ins['name'] == 'reorx'
        assert ins['nature']['luck'] == 10

    # requires test_build_instance
    def test_retrieval_operations(self):
        ins = self.S.build_instance(
            name='reorx',
            nature={
                'luck': 10
            },
            disks=[
                {
                    'is_primary': True,
                    'last_modified': datetime.datetime.now(),
                    'volums': []
                }
            ]
        )

        assert ins['name'] == ins.retrieval_get('name')
        assert ins['nature']['luck'] == ins.retrieval_get('nature.luck')
        assert ins['disks'][0]['is_primary'] == ins.retrieval_get('disks.[0].is_primary')

    # requires UtilitiesTest.test_build_dict
    def test_gen(self):
        assert isinstance(self.S.gen.id(), ObjectId)

        d = self.S.gen.nature()
        assert len(d.keys()) == 1 and d['luck'] == 0

        d = self.S.gen.disks.volums(name='EVA-01')
        assert hash_dict(d) == hash_dict(
            build_dict(self.S.struct['disks'][0]['volums'][0], name='EVA-01'))
