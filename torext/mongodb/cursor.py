#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymongo.cursor import Cursor as PymongoCursor
from collections import deque


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
            if isinstance(self._Cursor__data, deque):
                item = self._Cursor__data.popleft()
            else:
                item = self._Cursor__data.pop(0)
            if self._Cursor__manipulate:
                son = db._fix_outgoing(item, self._Cursor__collection)
            else:
                son = item
            if self.__wrap is not None:
                return self.__wrap(son, from_db=True)
            else:
                return son
        else:
            raise StopIteration

    def __getitem__(self, index):
        obj = super(Cursor, self).__getitem__(index)
        if (self.__wrap is not None) and isinstance(obj, dict):
            return self.__wrap(obj)
        return obj

#     def next(self):
#         db = self.__collection.database
#         if len(self.__data) or self._refresh():
#             if self.__manipulate:
#                 test.debug('__manipulate in cursor')
#                 # NOTE this line will return a SON object, which isnt used normally,
#                 # but may cause problems if leave orignial
#                 print '__data', type(self.__data), self.__data
#                 raw = db._fix_outgoing(self.__data.pop(0), self.__collection)
#             else:
#                 print '__data', type(self.__data), self.__data
#                 raw = self.__data.pop(0)

#             if self.__wrap is not None:
#                 test.debug('get wrap')
#                 return self.__wrap(raw, from_db=True)
#             else:
#                 test.debug('wrap unget')
#                 return raw
#         else:
#             raise StopIteration
