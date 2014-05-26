#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.errors import CommandArgumentError
from torext.script import Command

from nose.tools import assert_raises


def test_func_parse():
    def pri(a, b, c=True, d=3):
        print 'pri func'
        return

    c = Command(pri)
    assert c.parameters == ['a', 'b']
    assert c.keyword_parameters == {'c': True, 'd': 3}

    with assert_raises(CommandArgumentError):
        c.parse_args([])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a'])

    c.parse_args(['v a', 'v b'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c'])

    c.parse_args(['v a', 'v b', '--c', '1'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '1', '2'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '1', '2', '--d'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '--d'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '--d', '3'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '--d', '3'])

    c.parse_args(['v a', 'v b', '--c', '1', '--d', '3'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '1', '--d', '3', '4'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--x', '1'])

    with assert_raises(CommandArgumentError):
        c.parse_args(['v a', 'v b', '--c', '1', '--x', '2'])
