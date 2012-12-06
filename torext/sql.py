#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Features:
    * multiple databases (on different Model)
    * scope control for session in tornado environment
    * signal in commit process (use new api: orm.events)
    * signal in connection process

Finished:
    * bind all frequently-used classes & methods to SQLAlchemy object
    * Model class for creating new models
    * customizable Query object
"""

import os
import functools
import sqlalchemy
from sqlalchemy.engine.url import make_url
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base, declared_attr


#################
# Model & Query #
#################

class BaseQuery(orm.Query):
    pass


class _QueryProperty(object):

    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, owner):
        return self.sa.session.query(owner)


class _Model(object):
    query = None

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class SQLAlchemy(object):
    """
    Proper active sequence in app mode:

        app: app = TorextApp()
        |
        engine: db = SQLAlchemy
        |
        model: User(db.Model)

    non-app mode:

        engine: db = SQLAlchemy(uri, config={...})
        |
        model: User(db.Model)
    """

    def __init__(self, app=None, uri=None, config={}):
        # config
        if app:
            self.config = self.init_config(app.settings['SQLALCHEMY'])
        else:
            self.config = self.init_config(config)
        self.app = app
        if uri:
            self.config['uri'] = uri

        # engine
        self.engine = self.get_engine()

        # session
        self.session = self.create_scoped_session()

        # Model
        self.Model = self.make_declarative_base()

        self._include_sqlalchemy()

    def create_scoped_session(self, options={}):
        # TODO add options here
        #return orm.scoped_session(orm.sessionmaker(self.engine, query_cls=BaseQuery))
        return orm.scoped_session(orm.sessionmaker(self.engine))

    def make_declarative_base(self):
        base = declarative_base(cls=_Model, name='Model')
        #base.query = _QueryProperty(self)
        base.query = self.session.query_property()
        return base

    def _include_sqlalchemy(self):
        for module in sqlalchemy, sqlalchemy.orm:
            for key in module.__all__:
                if not hasattr(self, key):
                    setattr(self, key, getattr(module, key))
        # Note: self.Table does not attempt to be a SQLAlchemy Table class.
        self.Table = _make_table(self)
        self.relationship = _wrap_with_default_query_class(self.relationship)
        self.relation = _wrap_with_default_query_class(self.relation)
        self.dynamic_loader = _wrap_with_default_query_class(self.dynamic_loader)

    def init_config(self, incoming={}):
        config = {
            'uri': 'sqlite://',
            'binds': None,
            'pool_size': None,
            'pool_timeout': None,
            'pool_recycle': None
        }
        for k in config:
            if k in incoming:
                config[k] = incoming[k]
        return config

    def get_engine(self, bind=None):
        uri_obj = make_url(self.config['uri'])
        options = {
            'convert_unicode': True,
            'echo': self.config.get('echo', False)
        }
        for k in ('pool_size', 'pool_timeout', 'pool_recycle'):
            v = self.config.get(k, None)
            if v is not None:
                options[k] = v
        self._apply_driver_hacks(uri_obj, options)
        #engine = sqlalchemy.create_engine(uri_obj, **options)
        engine = sqlalchemy.create_engine(uri_obj)
        return engine

    def _apply_driver_hacks(self, uri_obj, options):
        if uri_obj.drivername == 'mysql':
            uri_obj.query.setdefault('charset', 'utf8')
            options.setdefault('pool_size', 10)
            options.setdefault('pool_recycle', 7200)
        elif uri_obj.drivername == 'sqlite':
            pool_size = options.get('pool_size')
            in_memory = False
            # we go to memory and the pool size was explicitly set to 0
            # which is fail.  Let the user know that
            if uri_obj.database in (None, '', ':memory:'):
                in_memory = True
                if pool_size == 0:
                    raise RuntimeError('SQLite in memory database with an '
                                       'empty queue not possible due to data '
                                       'loss.')
            # if pool size is None or explicitly set to 0 we assume the
            # user did not want a queue for this sqlite connection and
            # hook in the null pool.
            elif not pool_size:
                from sqlalchemy.pool import NullPool
                options['poolclass'] = NullPool

            # if it's not an in memory database we make the path absolute.
            if not in_memory and self.app:
                uri_obj.database = os.path.join(self.app.root_path, uri_obj.database)

    def _execute_operation(self, operation):
            op = getattr(self.Model.metadata, operation)
            op(self.engine)

    def create_all(self):
        self._execute_operation('create_all')

    def drop_all(self):
        self._execute_operation('drop_all')

    def reflect(self):
        self._execute_operation('reflect')

    def __repr__(self):
        return '<%s engine=%r>' % (
            self.__class__.__name__,
            self.config['SQLALCHEMY_DATABASE_URI']
        )


###############
# integration #
###############

def _make_table(db):
    def _Table(*args, **kwargs):
        """
        1. if passing (name, column, ..), existing metadata will be added to args,
           return Table(name, metadata, column, ..)
        2. add info={'bind_key': None} if not exists
        """
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
        info = kwargs.pop('info', None) or {}
        info.setdefault('bind_key', None)
        kwargs['info'] = info
        return sqlalchemy.Table(*args, **kwargs)
    return _Table


def _set_default_query_class(d):
    if 'query_class' not in d:
        d['query_class'] = BaseQuery


def _wrap_with_default_query_class(fn):
    @functools.wraps(fn)
    def newfn(*args, **kwargs):
        _set_default_query_class(kwargs)
        if "backref" in kwargs:
            backref = kwargs['backref']
            if isinstance(backref, basestring):
                backref = (backref, {})
            _set_default_query_class(backref[1])
        return fn(*args, **kwargs)
    return newfn
