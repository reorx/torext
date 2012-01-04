#!/usr/bin/python
# -*- coding: utf-8 -*-

# simple wrapper of MongoDB using pymongo
# NOTE this code is semi-manufactured, now using mongokit with torext
# in practicing product

__all__ = (
    'CollectionDeclarer', 'Document', 'ObjectId',
)

from pymongo.objectid import ObjectId
from pymongo.cursor import Cursor as PymongoCursor

from torext.utils.schema import StructedSchema

class CollectionDeclarer(object):
    connection = None

    def __init__(self, _db, _col):
        self._db = _db
        self._col = _col
        self.col = None
        self._fetch_col()

    def _fetch_col(self):
        if self.col is None:
            self.col = self.connection[self._db][self._col]

    def __get__(self, ins, owner):
        self._fetch_col()
        return self.col

# NOTE pymongo.collection only apply dict object to save
class Document(StructedSchema):
    """A wrapper of MongoDB Document, can also be used to init new document.

    Acturally, a Document is a representation of one certaion collectino which store
    data in structure of the Document, they two are of one-to-one relation

    Usage:
    1. create new document
    >>> class ADoc(Document):
    ...     col = CollectionDeclarer('dbtest', 'coltest')
    ...
    >>> d = ADoc()
    >>> d['name'] = 'abs'
    >>> d['_id']
    < ObjectId .. >
    >>> d.save()

    2. init from existing document
    >>> d = ADoc(exist_dict)
    >>> d.save()
    """
    __safe__ = True

    def __init__(self, raw=None):
        """ wrapper of raw data from cursor

        can also involved in normal use

        NOTE *without validation*
        """
        self._ = {}
        if raw is not None:
            self._.update(raw)
            self._in_db = True
        else:
            self._in_db = False

    def __getitem__(self, key):
        return self._[key]

    def save(self):
        self.col.save(self._, safe=self.__safe__)
        self._in_db = True

    def remove(self):
        assert self._in_db, 'could not remove not in db document'
        self.col.remove(self['_id'])
        # to prevent data assignments afterwords
        self._ = {}
        self._in_db = False

    #def autofix(self):
        #pass

################
    @classmethod
    def new(cls, input_dict=None):
        """Designed only to init from:
         1. existing plain (no _id) dict
         2. self struct

        NOTE *will validate struct*
        """
        ins = cls()

        if input_dict is None:
            ins._.update(cls.build_instance('main'))
        else:
            assert isinstance(input_dict, dict), 'mongodb document source should be dict'
            # validate
            ins.validate_main(input_dict)
            ins._.update(input_dict)
        ins._.update(_id=ObjectId())
        return ins

    @classmethod
    def find(cls, *args, **kwgs):
        kwgs['wrap'] = cls
        cursor = Cursor(cls.col, *args, **kwgs)
        return cursor

    @classmethod
    def one(cls, *args, **kwgs):
        cursor = cls.find(*args, **kwgs)
        count = cursor.count()
        if count >= 1:
            return cursor.next()

    @classmethod
    def by_strId(cls, strId):
        return cls.find(ObjectId(strId))

    def __str__(self):
        return 'Document: ' + str(self._)


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
                # NOTE this line will return a SON object, which isnt used normally,
                # but may cause problems if leave orignial
                return db._fix_outgoing(self.__data.pop(0), self.__collection)
            else:
                raw = self.__data.pop(0)
                if self.__wrap is not None:
                    return self.__wrap(raw)
                else:
                    return raw
        else:
            raise StopIteration

    def __getitem__(self, index):
        obj = super(Cursor, self).__getitem__(index)
        if isinstance(obj, dict):
            return self.__wrap(obj)
        return obj

