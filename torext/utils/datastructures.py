#!/usr/bin/python
# -*- coding: utf-8 -*-


class SDict(dict):
    """
    flexiblely set & get key-value
    """
    def __init__(self, raw=None):
        super(SDict, self).__init__()
        if raw is not None:
            assert isinstance(raw, dict), 'SDict initializing argument is not a dict'
            for k in raw.keys():
                self.__setattr__(k, raw[k])

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError

    def _reverse(self):
        d = {}
        for k in self.keys():
            d[k] = self[k]
        return d
