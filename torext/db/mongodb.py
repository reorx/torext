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
    'CollectionDeclarer', 'Document', 'ObjectId', 'oid',
)

import logging
import copy
from pymongo.objectid import ObjectId
from pymongo.cursor import Cursor as PymongoCursor

from torext.utils.debugtools import pprint
from torext.db.schema import StructedSchema
from torext import errors


def oid(id):
    if isinstance(id, ObjectId):
        return id
    elif isinstance(id, (str, unicode)):
        if isinstance(id, unicode):
            id = id.encode('utf8')
        return ObjectId(id)
    else:
        raise ValueError('get type %s, should str\unicode or ObjectId' % type(id))


class CollectionDeclarer(object):
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
        # NOTE this is the raw collection object from pymongo
        self.col = None
        self._fetch_col()

    def _fetch_col(self):
        if self.col is None:
            self.col = self.connection[self._db][self._col]

    def __get__(self, ins, owner):
        self._fetch_col()
        return self.col


class Document(StructedSchema):
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
    __safe__ = True
    __id_map__ = False
    # TODO key_map = {'id': '_id'}

    def __init__(self, raw=None):
        """ wrapper of raw data from cursor

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

    def __setitem__(self, key, value):
        self._[key] = value

    def __delitem__(self, key):
        del self._[key]

    def doc_get(self, dot_key):
        """
        raise IndexError or KeyError if can not get

        Example:
            'menu.file.name'
            'menu.ps.0.title'
        """
        def drag_out(o, klist):
            try:
                key = klist.pop(0)
            except IndexError:
                return o
            return drag_out(o[key], klist)

        return drag_out(self._, dot_key.split('.'))

    def doc_set(self, dot_key, value):
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        # TODO check if there is any problem with self.get(
        op = self.get('.'.join(keys))
        op[last_key] = value

    def doc_del(self, dot_key):
        """ seems no use.."""
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        op = self.get('.'.join(keys))
        del op[last_key]

    def doc_copy(self, exclude=[]):
        return copy.deepcopy(self._)

    #def autofix(self):
        #pass

    def identifier(self):
        return {'_id': self['_id']}

    @property
    def id(self):
        return self[self.__id_map__]

    def validate_self(self):
        self.__class__.validate(self._)

    #################
    # db operations #
    #################

    def save(self):
        self.validate_self()
        ro = self.col.save(self._,
                           manipulate=True,
                           safe=self.__safe__)
        # logging.info('mongodb:: save return id: %s' % ro)
        self._in_db = True
        return ro

    def remove(self):
        assert self._in_db, 'could not remove not in db document'
        self.col.remove(self['_id'])
        # to prevent data assignments afterwords
        self._ = {}
        self._in_db = False

    def update(self, to_update):
        ro = self.col.update(self.identifier(),
                to_update,
                safe=self.__safe__)
        return ro

    def col_set(self, index, value):
        return self.update({
            '$set': {index: value}
        })

    def col_inc(self, index, value):
        return self.update({
            '$inc': {index: value}
        })

    def col_push(self, index, value):
        return self.update({
            '$push': {index: value}
        })

    #################
    # class methods #
    #################

    @classmethod
    def new(cls, **kwgs):
        """Designed only to init from self struct
        """
        ins = cls()
        # now ins._in_db is False
        if 'default' in kwgs:
            default = kwgs.pop('default')
        else:
            default = {}
        ins._.update(cls.build_instance(default=default))
        if ins.__id_map__:
            ins['_id'] = ins['id']
        else:
            ins['_id'] = ObjectId()
        logging.info('mongodb:: generated id: %s' % ins['_id'])
        return ins

    @classmethod
    def find(cls, *args, **kwgs):
        # TODO compability of 'id' and '_id' in str type
        # as to 'id', '__id_map__' value should be judged first
        kwgs['wrap'] = cls
        cursor = Cursor(cls.col, *args, **kwgs)
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
    def exist(cls, *args, **kwgs):
        try:
            return cls.one(*args, **kwgs)
        except errors.ObjectNotFound:
            return None

    @classmethod
    def by_oid(cls, id, key='_id'):
        if isinstance(id, (str, unicode)):
            id = ObjectId(id)
        return cls.one({key: id})

    def __str__(self):
        return 'Document: ' + repr(self._)

    def _pprint(self):
        pprint(self._)


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
                logging.debug('manipulate in cursor')
                # NOTE this line will return a SON object, which isnt used normally,
                # but may cause problems if leave orignial
                raw = db._fix_outgoing(self.__data.pop(0), self.__collection)
            else:
                raw = self.__data.pop(0)

            if self.__wrap is not None:
                logging.debug('get wrap')
                return self.__wrap(raw)
            else:
                logging.debug('wrap unget')
                return raw
        else:
            raise StopIteration

    def __getitem__(self, index):
        obj = super(Cursor, self).__getitem__(index)
        if isinstance(obj, dict):
            return self.__wrap(obj)
        return obj

