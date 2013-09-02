#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext import utils


def test_generate_cookie_secret():
    assert utils.generate_cookie_secret()


def test_json_decode():
    assert isinstance(utils.json_decode('{"a": 1}'), dict)


def test_json_encode():
    assert isinstance(utils.json_encode({"a": 1}), str)


def test_timesince():
    import datetime
    assert utils.timesince(datetime.datetime.now())
