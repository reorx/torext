#!/usr/bin/python
# -*- coding: utf-8 -*-


#from torext.db.mongodb import ObjectId
from torext.db.mongodb.struct import StructuredDict, Struct, ObjectId

from torext.lib.testing import _TestCase


class TestFunction(_TestCase):

    def setUp(self):
        self.doc = {
            'object_id': None,
            'name': 'reorx is the god',
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
        some_doc = {
            'extra': 'you never know',

            'id': ObjectId(),
            'name': 'fucker',
            'description': u' dou zhan hao, enn? ass we can',
            'flag': None,
            'number': long(123),
            'ab': 4.9999,
            'bilis': [
                {
                    'biliname': 'gbl',
                    'yoo': 1,
                    'DTPD': [
                        '12:22',
                        '23:11'
                    ]
                },
                {
                    'biliname': 'sdl',
                    'yoo': 0,
                    'DTPD': [
                        '02:22',
                        '04:19',
                        '14:18'
                    ]
                }
            ]
        }

        self.doc = some_doc

    def test_validate_dict(self):
        struct = {
            'id': ObjectId,
            'name': unicode,
            'description': str,
            'flag': str,
            'number': int,
            'ab': float,
            'bilis': [
                {
                    'biliname': str,
                    'yoo': int,
                    'DTPD': [str]
                }
            ]
        }

        validate_dict(self.doc, struct,
                        [str],
                        [
                            (str, unicode),
                            (int, long),
                        ])

        def test_map_dict(self):
            pass

        def test_index_dict(self):
            pass

        def test_hash_dict(self):
            pass


class TestStruct(_TestCase):
    def setUp(self):

        class SomeStruct(StructuredDict):
            struct = Struct({
                'id': ObjectId,
                'name': str,
                'description': unicode,
                'flag': str,
                'bilis': [
                    {
                        'biliname': str,
                        'yoo': int,
                        'DTPD': [
                            {'datetime': str}
                        ],
                        'dt': {
                            'guy': str
                        }
                    }
                ]
            })

            default_values = {
                'flag': 'fuck-you',
            }

            allow_None_types = [
                str,
            ]

        self.Struct = SomeStruct

    def test_build_instance(self):

        ins = self.Struct.build_instance(
            default={
                'name': 'star',
                'bilis': [
                    SomeStruct.gen.bilis(default={
                        'DTPD': [
                            SomeStruct.gen.bilis.DTPD(default={
                                'datetime': '12:32'
                            })
                        ]
                    })
                ]
            }
        )


        ins.validate()

        print ins.inner_get('bilis.[0].dt')
        #logger.info('%s: \n%s' % (type(ins), ins))

        #logger.info('----------')

        #logger.info(repr(SomeStruct.gen.bilis.biliname()))
