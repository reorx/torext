#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from torext.app import TorextApp
from torext.sql import SQLAlchemy

app = TorextApp()
app.settings['DEBUG'] = False
app.settings['SQLALCHEMY'] = {
    'uri': 'mysql://reorx:mx320lf2@localhost/test_sa'
}
app.setup()
db = SQLAlchemy(app=app)

db.drop_all()

#sys.exit()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))


db.create_all()


u = User(name='reorx')
db.session.add(u)
db.session.commit()

cur = User.query.filter_by(name='reorx')

print cur


db.drop_all()
