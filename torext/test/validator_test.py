#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nose.tools import *
from torext.validators import Field, RegexField, WordField,\
    EmailField, URLField, IntstringField, Params
from torext.errors import ValidationError


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
    field = RegexField(pattern=pattern)
    if result:
        field.validate(match)
    else:
        with assert_raises(ValidationError):
            field.validate(match)


def test_words():
    pass


def test_email():
    pass


def test_url():
    pass


def test_intstring():
    pass


class FakeParams(Params):
    id = IntstringField('wat are you?', required=True, min=1)
    name = WordField('name should be 8', required=True, max=8)
    email = EmailField('email not valid in format', required=True)
    content = Field('content should be < 20', max=20)


def test_param():
    data_pairs = [
        ({
            'id': '1',
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
            'id': 999
        }, 2),
        ({
            'content': 'The project to complete the final episodes (retelling episodes 25 and 26 of the series) was completed later in 1997 and released on July 19 as The End of Evangelion. '
        }, 4)
    ]

    for data, error_num in data_pairs:
        yield check_param, data, error_num


def check_param(data, error_num):
    params = FakeParams(**data)
    print error_num, len(params._errors), params._errors
    assert error_num == len(params._errors)
