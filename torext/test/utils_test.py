#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext import utils


def test_generate_cookie_secret():
    assert utils.generate_cookie_secret()


def test__dict():
    assert isinstance(utils._dict('{"a": 1}'), dict)


def test__json():
    assert isinstance(utils._json({"a": 1}), str)


def test_timesince():
    import datetime
    assert utils.timesince(datetime.datetime.now())
