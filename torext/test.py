#!/usr/bin/python
# -*- coding: utf-8 -*-
from mongodb import *
from pymongo import Connection
import logging

if '__main__' == __name__:
    logging.basicConfig(level=logging.DEBUG)
    conn = Connection()

    class Collection(CollectionDeclarer):
        connection = conn

    class TestDoc(Document):
        col = Collection('test', 'doc')
        struct_main  = {
            'name': str,
            'pow': list,
        }

    # test new empty
    doc = TestDoc.new()
    print doc

    # test new exist
    data = {
        'name': 'reorx',
        'pow': [ 1,2,3 ]
    }
    doc = TestDoc.new(data)
    print doc
