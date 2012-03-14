#!/usr/bin/python
# -*- coding: utf-8 -*-

# totally a mass, wait for changing..

import logging
logging.getLogger().setLevel('DEBUG')

###############
# settings.py #
###############
connections_opts = {
    'mongodb': {
        'core': {
            'enable': True,
            'host': '127.0.0.1',
            'port': 27017,
            'username': None,
            'password': None,
            'keep_time': 7200,
        }
    }
}


###############
# __init__.py #
###############

from torext.db.connections import Connections
connections = Connections.instance(connections_opts)

print connections

mdb = connections.get('mongodb', 'core')
print mdb

#############
# models.py #
#############

from torext.db.mongodb import *

class CollectionDeclarer(CollectionDeclarer):
    connection = connections.get('mongodb', 'core')

class TestDoc(Document):
    col = CollectionDeclarer('test', 'col0')
    __id_map__ = True
    struct = {
        'id': ObjectId,
        'name': str,
        'age': int,
    }

td = TestDoc.new()

print td

td.save()

import logging
from mongodb import *
from pymongo import Connection

from torext.logger import streamHandler
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)
if '__main__' == __name__:
    conn = Connection()

    class Collection(CollectionDeclarer):
        connection = conn

    class TestDoc(Document):
        col = Collection('test', 'doc')
        struct_main  = {
            'name': str,
            'pow': list,
        }
        struct_foo = {
            'user_id': int
        }

    # test validate any
    TestDoc.validate({'user_id':int}, 'foo')
    print 'validation passed'

    # test new empty
    doc = TestDoc.new()
    print doc

    # test new exist
    data = {
        'name': 'reorx',
        'pow': [ 1,2,3 ],
        'spirit': 1.2
    }
    doc = TestDoc.new(data)
    print doc

    # test save
    ro = doc.save()
    print 'after save', doc#, type(ro)

    # test find
    fd = TestDoc.find({'_id': ro})[0]
    print 'find out: ', fd

    # test modify
    fd['pow'] = [5,9,7]
    fd.save()
    print 'find after modify: ', TestDoc.one({'_id': ro})

    # test modify
    del fd['pow']
    fd.save()
    print 'find after delete: ', TestDoc.by_id(str(ro))

    # test find multi results
    qro = TestDoc.find({'name': 'reorx'})[1:40]
    print qro

    # test find unicode
    qro = TestDoc.find({u'name': u'reorx'})
    print 'unicode find ', qro.count()
