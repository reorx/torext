#!/usr/bin/env python
# -*- coding: utf-8 -*-

# simple orm wrapper of MongoDB using pymongo

import copy
import logging
from torext import errors
from bson.objectid import ObjectId
from pymongo.collection import Collection
from .dstruct import StructuredDict
from .cursor import Cursor


def oid(id):
    if isinstance(id, ObjectId):
        return id
    elif isinstance(id, (str, unicode)):
        if isinstance(id, unicode):
            id = id.encode('utf8')
        return ObjectId(id)
    else:
        raise ValueError('get type %s, should str\unicode or ObjectId' % type(id))


class DocumentMetaclass(type):
    """
    use for judging if Document's subclasses have assign attribute 'col' properly
    """
    def __new__(cls, name, bases, attrs):
        # judge if the target class is Document
        if not (len(bases) == 1 and bases[0] is StructuredDict):
            if not ('col' in attrs and isinstance(attrs['col'], Collection)):
                raise errors.ConnectionError(
                    'col of a Document is not set properly, passing: %s %s' %
                    (attrs['col'], type(attrs['col'])))

        return type.__new__(cls, name, bases, attrs)


class Document(StructuredDict):
    """A wrapper of MongoDB Document, can also be used to init new document.

    Acturally, a Document is a representation of one certaion collectino which store
    data in structure of the Document, they two are of one-to-one relation

    Usage:
    1. create new document
    >>> class ADoc(Document):
    ...     col = mongodb['dbtest']['coltest']
    ...

    2. init from existing document

    """
    __metaclass__ = DocumentMetaclass

    __safe_operation__ = True

    def __init__(self, raw=None, from_db=False):
        """ wrapper of raw data from cursor

        NOTE *initialize without validation*
        """
        if raw is None:
            super(Document, self).__init__()
        else:
            super(Document, self).__init__(raw)

        self._in_db = from_db

    def __str__(self):
        return '<Document: %s >' % dict(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    @property
    def identifier(self):
        return {'_id': self['_id']}

    def _get_operate_options(self, **kwgs):
        options = {
            'w': self.__class__.__safe_operation__ and 1 or 0
        }
        options.update(kwgs)
        return options

    def save(self):
        self.validate()
        rv = self.col.save(self, **self._get_operate_options(manipulate=True))
        logging.debug('MongoDB: ObjectId(%s) saved' % rv)
        self._in_db = True
        return rv

    def remove(self):
        assert self._in_db, 'could not remove document which is not in database'
        self._history = self.copy()
        _id = self['_id']
        self.col.remove(_id, **self._get_operate_options())
        logging.debug('MongoDB: %s removed' % self)
        self = Document()

    def update_doc(self, doc, **kwgs):
        rv = self.col.update(self.identifier, doc, self._get_operate_options(**kwgs))
        return rv

    @classmethod
    def new(cls, **kwgs):
        """
        initialize by structure of self.struct
        """
        instance = cls.build_instance(**kwgs)
        instance['_id'] = ObjectId()
        logging.debug('MongoDB: _id generated %s' % instance['_id'])
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
            raise errors.MultipleObjectsReturned('multi results found in Document.one,\
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
