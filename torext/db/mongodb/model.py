#!/usr/bin/python
# -*- coding: utf-8 -*-

# simple wrapper of MongoDB using pymongo
# NOTE this code is semi-manufactured, now using mongokit with torext
# in practicing product

# NOTE pymongo.collection only apply dict object to save
# TODO django manager like attribute binding with Document,
# use for attaching logical-data-operation packed functions.
# Philosophe:
#
# * application level involvings
#           ^
#           |
#   [middleware attach to models]
#           |
# * functional data operation (packed functions)
#           ^
#           |
# * bottom data storage (database)

__all__ = (
    '_CollectionDeclarer', 'Document', 'Struct', 'ObjectId', 'oid',
)

import copy
import logging
from torext import errors
from pymongo.objectid import ObjectId
from .dstruct import Struct, StructuredDict
from .base import Cursor


test = logging.getLogger('test')
test.setLevel(logging.INFO)


def oid(id):
    if isinstance(id, ObjectId):
        return id
    elif isinstance(id, (str, unicode)):
        if isinstance(id, unicode):
            id = id.encode('utf8')
        return ObjectId(id)
    else:
        raise ValueError('get type %s, should str\unicode or ObjectId' % type(id))


class _CollectionDeclarer(object):
    connection = None

    def __init__(self, _db, _col):
        if self.connection is None:
            from torext.errors import ConnectionError
            raise ConnectionError("""
                MongoDB connection is None in CollectionDeclarer,
                it may happen when your settings.py file is incorrect,
                or you involve the project in an outer place without properly configuration.
                """)
        self._db = _db
        self._col = _col
        # self.col = None
        # self._fetch_col()
        self.col = self.connection[self._db][self._col]

    # def _fetch_col(self):
    #     if self.col is None:

    def __get__(self, ins, owner):
        # if self.col is None:
        #     self.col = self.connection[self._db][self._col]
        return self.col


class Document(StructuredDict):
    """A wrapper of MongoDB Document, can also be used to init new document.

    Acturally, a Document is a representation of one certaion collectino which store
    data in structure of the Document, they two are of one-to-one relation

    Usage:
    1. create new document
    >>> class ADoc(Document):
    ...     col = CollectionDeclarer('dbtest', 'coltest')
    ...

    2. init from existing document

    """
    __write_safe__ = True
    # __id_map__ = False

    def __init__(self, raw={}, from_db=False):
        """ wrapper of raw data from cursor

        NOTE *without validation*
        """
        self._in_db = False
        if from_db:
            self._in_db = True

        super(Document, self).__init__(raw)

    def __str__(self):
        return '<Document: %s >' % dict(self)

    def copy(self, exclude=[]):
        return copy.deepcopy(dict(self))

    @property
    def identifier(self):
        return {'_id': self['_id']}

    #################
    # db operations #
    #################

    def save(self):
        test.debug('mongodb: call save()')
        self.validate()
        ro = self.col.save(self,
                           manipulate=True,
                           safe=self.__write_safe__)
        test.debug('mongodb: ObjectId(%s) saved' % ro)
        self._in_db = True
        return ro

    def remove(self):
        assert self._in_db, 'could not remove document which is not in database'
        self._history = self.copy()
        self.col.remove(self['_id'])
        self = Document()

    # def update(self, to_update):
    #     ro = self.col.update(self.identifier,
    #             to_update,
    #             safe=self.__write_safe__)
    #     return ro

    # def col_set(self, index, value):
    #     return self.update({
    #         '$set': {index: value}
    #     })

    # def col_inc(self, index, value):
    #     return self.update({
    #         '$inc': {index: value}
    #     })

    # def col_push(self, index, value):
    #     return self.update({
    #         '$push': {index: value}
    #     })

    #################
    # class methods #
    #################

    @classmethod
    def new(cls, default={}):
        """
        init by structure of self.struct
        """
        # ins = cls()
        # ins.update(cls.build_instance(default=default))
        # if ins.__id_map__:
        #     ins['_id'] = ins['id']
        # else:
        #     ins['_id'] = ObjectId()
        # test.debug('mongodb:: generated id: %s' % ins['_id'])
        # return ins

        instance = cls.build_instance(default=default)
        # '_id' will not be seen by .validate()
        instance['_id'] = ObjectId()
        test.debug('generate _id by model: %s' % instance['_id'])
        return instance

    @classmethod
    def find(cls, *args, **kwgs):
        kwgs['wrap'] = cls
        cursor = Cursor(cls.col, *args, **kwgs)
        return cursor

    @classmethod
    def exist(cls, *args, **kwgs):
        """
        just do the same query as 'find', but will return None if nothing in the cursor.
        """
        cursor = cls.find(*args, **kwgs)
        if cursor.count() == 0:
            return None
        return cursor

    @classmethod
    def one(cls, *args, **kwgs):
        cursor = cls.find(*args, **kwgs)
        count = cursor.count()
        if count == 0:
            raise errors.ObjectNotFound('query dict: ' + repr(args[0]))
        if count > 1:
            raise errors.MultiObjectsReturned('multi results found in Document.one,\
                    query dict: ' + repr(args[0]))
        return cursor.next()

    @classmethod
    def by__id(cls, id):
        assert isinstance(id, ObjectId), 'You must use ObjectId object in by_oid() method'
        return cls.one({'_id': id})

    @classmethod
    def by__id_str(cls, id_str):
        id = ObjectId(id_str)
        return cls.one({'_id': id})
