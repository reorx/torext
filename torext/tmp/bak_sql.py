#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# An intergration of sqlalchemy

__all__ = (
    'Column', 'Table', 'ForeignKey', 'Sequence',
    'Integer', 'BigInteger', 'Float',
    'String', 'Text', 'Boolean',
    'Date', 'DateTime',
    'relationship',
    'MySQLModel', 'mysql',
    )

from sqlalchemy import (
    Column, Table, ForeignKey, Sequence,
    Integer, BigInteger, Float,
    String, Text, Boolean,
    Date, DateTime,
    )

from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base, declared_attr

from .connections import connections

mysql = connections.get('mysql', 'master')


class _Model(object):
    id = Column(Integer, primary_key=True)
    # NOTE #1 temporarily use binded attribute `query` for compatible
    query = None

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    # NOTE -> #1
    @classmethod
    def by_id(cls, id):
        qs = cls.query.filter_by(id=id).first()
        if not qs:
            return None
        return qs

    # NOTE -> #1
    def save(self, **kwgs):
        if kwgs:
            for k, v in kwgs.iteritems():
                setattr(self, k, v)
        mysql.session.add(self)
        mysql.session.commit()

MySQLModel = declarative_base(
        cls=_Model,
        name='MySQLModel',
        bind=mysql.engine
        )
# NOTE -> #1
MySQLModel.query = mysql.session.query_property()
