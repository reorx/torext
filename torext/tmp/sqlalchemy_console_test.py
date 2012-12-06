#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Notes:
    1. create_all must be called before any data communication
    2. primary_key is of no need to be set; manually set is allowed; it will count from the biggest if auto set;
"""


from nose.tools import *


from torext.sqlalchemy import SQLAlchemy


def phead(s):
    print '\n-- %s --' % s


phead('init db')
db = SQLAlchemy()
phead('end init db')

db.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://reorx:mx320lf2@localhost/test_sa'


class God(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

print God.metadata.bind

db.create_all()

#phead('get_binds')
#print db.get_binds()

phead('query_class')
print God.query_class, type(God.query_class)

phead('users')
print God.query.all()


u = God()
u.name = 'reorx'

db.session.add(u)

phead('1 commit')
db.session.commit()

u.name = 'eva0'
phead('2 commit')
db.session.commit()

#db.session.add(u)
#phead('3 commit')
#db.session.commit()

phead('users')
print God.query.all()


from torext.utils import start_shell

start_shell(globals())
