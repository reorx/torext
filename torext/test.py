#!/usr/bin/python
# -*- coding: utf-8 -*-
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
