#!/usr/bin/python
# -*- coding: utf-8 -*-

# MongoDB using pymongo

from pymongo.objectid import ObjectId

from .connections import connections

class MongoDBCollection(object):
    """A wrapper of MongoDB Document,
    can also be used to init new document.
    Usage:
    1. create new document
    >>> class ADoc(MongoDBCollection):
    >>>     c = mongoc('master', 'xxoo')
    >>>
    >>> d = ADoc()
    >>> d._['name'] = 'abs'
    >>> d.save()

    2. update existing document
    >>> d = ADoc()
    >>> d._.update(exist_dict)
    >>> d.save()
    """
    c = None
    __safe__ = True

    def __init__(self, row=None):
        if self.c is None:
            raise NotImplementedError('MongoDB Collection Undefined')
        if row is not None:
            assert isinstance(row, dict), 'mongodb document source should be dict'
            self._ = row
            self._is_new = False
        else:
            self._ = {
                '_id': ObjectId(),
            }
            self._is_new = True

    def save(self):
        self.c.save(self._, safe=self.__safe__)
        self._is_new = False

    def update(self, **kwgs):
        self._.update(kwgs)
        self.save()

    def remove(self):
        if not self._is_new:
            self.c.remove(self._['_id'])
        # to prevent data assignments afterwords
        self._ = None

    @classmethod
    def find_one(cls, id):
        return cls.c.find_one(ObjectId(id))

    @classmethod
    def find(cls, *args, **kwgs):
        return cls.c.find(*args, **kwgs)

    @classmethod
    def insert(cls, d):
        """
        Insert doc (or docs)
        """
        return cls.c.insert(d, safe=cls.__safe__)

    @classmethod
    def replace_by_id(cls, id, d):
        ins = cls(d)
        ins._['_id'] = ObjectId(id)
        ins.save()
        return

def mongoc(database, collection):
    """ mongodb collection """
    db = connections.get('mongodb', database)
    return getattr(db, collection)
