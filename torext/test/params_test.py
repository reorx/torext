#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from nose.tools import assert_raises
from torext import params
from torext.errors import ValidationError, ParamsInvalidError


def test_regex():
    pairs = [
        (r'^\w+', 'hell*', True),
        (r'^\w+', '*ello', False),

        (r'\w+$', 'hell*', False),
        (r'\w+$', '*ello', True),

        (r'^\w+$', 'hello', True),
        (r'^\w+$', '*ello', False),
        (r'^\w+$', 'hell*', False)
    ]

    for pattern, match, result in pairs:
        yield check_regex, pattern, match, result


def check_regex(pattern, match, result):
    field = params.RegexField(pattern=pattern)
    if result:
        field.validate(match)
    else:
        with assert_raises(ValidationError):
            field.validate(match)


def test_words():
    f0 = params.WordField()
    f0.validate('')
    f0.validate('goodstr')
    with assert_raises(ValidationError):
        f0.validate('should not contain space')
    with assert_raises(ValidationError):
        f0.validate('andother*(*^&')

    f1 = params.WordField(length=(4, 8))
    f1.validate('asdf')
    f1.validate('asdfasdf')
    with assert_raises(ValidationError):
        f1.validate('s')
    with assert_raises(ValidationError):
        f1.validate('longggggg')

    f2 = params.WordField(null=False)
    with assert_raises(ValidationError):
        f2.validate('')


def test_email():
    pairs = [
        ('i@t.cn', True),
        ('longname@longdomain.cn', True),
        ('nor@mal.thr', True),
        ('nor@mal.four', True),
        ('nor@mal.fivee', True),
        ('nor@mal.sixxxx', True),
        ('nor@mal.sevennnn', False),
        ('nor@mal', False),
        ('@mal.com', False),
    ]
    for email, result in pairs:
        yield check_email, email, result


def check_email(email, result):
    f = params.EmailField()
    if result:
        f.validate(email)
    else:
        assert_raises(ValidationError, f.validate, email)
        pass


def test_url():
    pairs = [
        ('http://hello.com', True),
        ('https://askdjfasdf.asdfasdf.com/', True),
        ('ftp://www.google.com', True),
        ('ssh://www.google.com', False),
        ('http://have.punc*tu*rat@ions.com', False),
        ('http://a.b.c.d.e.f.g.com', True),
        ('http://t.cn/@#$#$(*&', True),
    ]
    for url, result in pairs:
        yield check_url, url, result


def check_url(url, res):
    f = params.URLField()
    if res:
        f.validate(url)
    else:
        assert_raises(ValidationError, f.validate, url)


def test_intstring():
    pairs = [
        ('a', False),
        ('0b', False),
        ('1', True),
        ('2', False, {'min': 3}),
        ('100', False, {'max': 99}),
        ('1023', False, {'min': 1024, 'max': 1024}),
        ('1024', True, {'min': 1024, 'max': 1024}),
        ('1025', False, {'min': 1024, 'max': 1024}),
    ]
    for args in pairs:
        yield check_intstring, args


def check_intstring(args):
    kwgs = {}
    if len(args) > 2:
        kwgs = args[2]
    f = params.IntegerField(**kwgs)
    if args[1]:
        f.validate(args[0])
    else:
        assert_raises(ValidationError, f.validate, args[0])


def test_uuidstring():
    pairs = [
        ('asdf', False),
        ('1234', False),
        ('216edfae-19c0-11e3-9e93-10604b8a89ab', True)
    ]

    for s, res in pairs:
        yield check_uuidstring, s, res


def check_uuidstring(s, res):
    f = params.UUIDField()
    if res:
        f.validate(s)
    else:
        with assert_raises(ValidationError):
            f.validate(s)


def test_simple_list():
    list_field = params.ListField(choices=['a', 'b', 'c'])

    list_field.validate(['a'])
    list_field.validate(['a', 'b', 'c'])

    with assert_raises(ValidationError):
        list_field.validate(['b', 'c', 'd'])
    with assert_raises(ValidationError):
        list_field.validate(['z', 'a', 'b'])


def test_type_list():
    list_field = params.ListField(item_field=params.IntegerField(min=1, max=9), choices=[1, 2, 3])

    list_field.validate(['1', '2', '3'])
    with assert_raises(ValidationError):
        list_field.validate(['0', '1', '2'])
    with assert_raises(ValidationError):
        list_field.validate(['1', '2', '3', '4'])
    with assert_raises(ValidationError):
        list_field.validate(['a', '2', '3'])


class FakeParams(params.ParamSet):
    id = params.IntegerField('wat are you?', required=True, min=0)
    name = params.WordField('name should be 8', required=True, length=(1, 8))
    email = params.EmailField('email not valid in format', required=True)
    content = params.Field('content should be < 20', length=(1, 20))


def test_param():
    data_pairs = [
        ({
            'id': '0',
            'name': 'asuka',
            'email': 'asuka@nerv.com'
        }, 0),
        ({
            'id': '2',
            'name': 'lilith',
            'email': 'l@eva.com',
            'content': 'with adon'
        }, 0),
        ({
            'id': 'a3',
            'name': 'ayanami',
            'email': 'rei@nerv.com'
        }, 1),
        ({
            'id': 'b3',
            'name': 'shinjigivebackmyayanami',
            'email': 'yikali@nerv.com'
        }, 2),
        ({
            'id': 'c4',
            'name': 'E V A',
            'email': 'eva@god',
            'content': 'Gainax launched a project to create a movie ending for the series in 1997. The company first released Death and Rebirth on March 15'
        }, 4),
        ({}, 3),
        ({
            'id': 'd5'
        }, 3),
        ({
            'id': '999'
        }, 2),
        ({
            'content': 'The project to complete the final episodes (retelling episodes 25 and 26 of the series) was completed later in 1997 and released on July 19 as The End of Evangelion. '
        }, 4)
    ]

    for data, error_num in data_pairs:
        yield check_param, data, error_num


def check_param(data, error_num):
    params = FakeParams(**data)
    print error_num, len(params.errors), params.errors
    assert error_num == len(params.errors)


PARAMS_ID_MSG = 'id shoud be int larger than 1'
PARAMS_TOKEN_MSG = 'token should be a 32 length string'
PARAMS_TAG_MSG = 'tag should be word without punctuations, less than 8 characters'
PARAMS_FROM = 'from should be less than 8 characters'


class WebTestCase(unittest.TestCase):
    def setUp(self):
        from torext.app import TorextApp
        from torext.handlers import BaseHandler

        app = TorextApp()

        class APIParams(params.ParamSet):
            id = params.IntegerField(PARAMS_ID_MSG, required=True, min=1)
            token = params.Field(PARAMS_TOKEN_MSG, required=True, length=32)

            tag = params.WordField(PARAMS_TAG_MSG, length=8, default='foo')
            from_ = params.WordField(PARAMS_FROM, key='from', required=False, length=16)
            text_anyway = params.WordField()
            text_not_null = params.WordField(null=False)

        @app.route('/api')
        class APIHandler(BaseHandler):
            @APIParams.validation_required
            def get(self):
                print 'arguments', self.request.arguments
                print 'params', self.params
                self.write_json(self.params.to_dict(include_none=True))
                pass

            def post(self):
                self.write('ok')
                pass

        # let exceptions raised in handler be rethrowed in test function
        self.c = app.test_client(raise_handler_exc=True)

    def tearDown(self):
        self.c.close()

    def test_good(self):
        print 'test good'
        resp = self.c.get('/api', {
            'id': 1,
            'token': '0cc175b9c0f1b6a831c399e269772661'
        })
        assert resp.code == 200
        data = json.loads(resp.body)
        assert data['id'] == 1
        assert data['token'] == '0cc175b9c0f1b6a831c399e269772661'
        assert data['tag'] == 'foo'
        assert data['from'] is None

    def test_bad_id(self):
        resp = self.c.get('/api', {
            'id': 'a2',
            'token': '0cc175b9c0f1b6a831c399e269772661'
        })
        assert resp.code == 500
        self.assertRaises(ParamsInvalidError, self.c.get_handler_exc)

    def test_bad_token(self):
        resp = self.c.get('/api', {
            'id': '1',
            'token': '1c399e26977266'
        })
        assert resp.code == 500
        self.assertRaises(ParamsInvalidError, self.c.get_handler_exc)

    def test_bad_tag(self):
        resp = self.c.get('/api', {
            'id': '1',
            'token': '0cc175b9c0f1b6a831c399e269772661',
            'tag': 'good man'
        })
        assert resp.code == 500
        self.assertRaises(ParamsInvalidError, self.c.get_handler_exc)

    def test_null(self):
        resp = self.c.get('/api', {
            'id': 1,
            'token': '0cc175b9c0f1b6a831c399e269772661',
            'text_anyway': ''
        })
        assert resp.code == 200
        data = json.loads(resp.body)
        print 'data', data
        assert data['text_anyway'] == ''

        resp = self.c.get('/api', {
            'id': 1,
            'token': '0cc175b9c0f1b6a831c399e269772661',
            'text_anyway': '',
            'text_not_null': ''
        })
        assert resp.code == 500


if __name__ == '__main__':
    unittest.main()
