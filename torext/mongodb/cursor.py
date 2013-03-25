#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymongo.cursor import Cursor as PymongoCursor


class Cursor(PymongoCursor):
    def __init__(self, *args, **kwargs):
        self.__wrap = None
        if kwargs:
            self.__wrap = kwargs.pop('wrap', None)
        super(Cursor, self).__init__(*args, **kwargs)

    def next(self):
        if self._Cursor__empty:
            raise StopIteration
        db = self._Cursor__collection.database
        if len(self.__data) or self._refresh():
            if self._Cursor__manipulate:
                d = db._fix_outgoing(self._Cursor__data.popleft(), self._Cursor__collection)
            else:
                d = self._Cursor__data.popleft()
            if self.__wrap:
                return self.__wrap(d, from_db=True)
            else:
                return d
        else:
            raise StopIteration

    def __getitem__(self, index):
        rv = super(Cursor, self).__getitem__(index)
        if self.__wrap and isinstance(rv, dict):
            return self.__wrap(rv)
        return rv
