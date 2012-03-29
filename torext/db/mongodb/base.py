#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from pymongo.cursor import Cursor as PymongoCursor


test = logging.getLogger('test')


class Cursor(PymongoCursor):
    def __init__(self, *args, **kwargs):
        self.__wrap = None
        if kwargs:
            self.__wrap = kwargs.pop('wrap', None)
        super(Cursor, self).__init__(*args, **kwargs)

    def next(self):
        #if self.__empty:
            #raise StopIteration
        #db = self.__collection.database
        #if len(self.__data) or self._refresh():
            #next = db._fix_outgoing(self._Cursor__data.pop(0), self._Cursor__collection, wrap=self.__wrap)
        #else:
            #raise StopIteration
        #return next
        #if self.__empty:
            #raise StopIteration
        db = self.__collection.database
        if len(self.__data) or self._refresh():
            if self.__manipulate:
                test.debug('__manipulate in cursor')
                # NOTE this line will return a SON object, which isnt used normally,
                # but may cause problems if leave orignial
                raw = db._fix_outgoing(self.__data.pop(0), self.__collection)
            else:
                raw = self.__data.pop(0)

            if self.__wrap is not None:
                test.debug('get wrap')
                return self.__wrap(raw, from_db=True)
            else:
                test.debug('wrap unget')
                return raw
        else:
            raise StopIteration

    def __getitem__(self, index):
        obj = super(Cursor, self).__getitem__(index)
        if isinstance(obj, dict):
            return self.__wrap(obj)
        return obj
