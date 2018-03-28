#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Features:
    * scope control for session in tornado environment
    * signal in commit process (use new api: orm.events)
    * signal in connection process

Finished:
    * bind all frequently-used classes & methods to SQLAlchemy object
    * Model class for creating new models
    * customizable Query object
"""

import os
import json
import logging
import functools
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import func
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, scoped_session, Query, load_only
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.mutable import Mutable

from torext.app import TorextApp
from torext.errors import TorextException


# TODO refine
logger = logging.getLogger('sqlalchemy')
logger.propagate = 0


class DoesNotExist(TorextException):
    pass


class MultipleObjectsReturned(TorextException):
    pass


def _make_table(db):
    def _Table(*args, **kwargs):
        """
        if passing (name, column, ..), existing metadata will be added to args,
        return Table(name, metadata, column, ..)
        """
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
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
            if isinstance(backref, str):
                backref = (backref, {})
            _set_default_query_class(backref[1])
        return fn(*args, **kwargs)
    return newfn


class BaseQuery(Query):
    """
    Add any function on this class, so that it can be called on SomeModel.query
    """
    @property
    def entity_class(self):
        return self._entities[0].entities[0].class_

    def _raise_not_exist(self, query_repr, message=None):
        if not message:
            message = '{} does not exist: {}'.format(self.entity_class.__name__, query_repr)
        raise self.entity_class.DoesNotExist(message)

    def _raise_multiple_results(self, query_repr):
        message = '{} got multiple objects: {}'.format(self.entity_class.__name__, query_repr)
        raise MultipleObjectsReturned(message)

    def get_or_raise(self, id, message=None):
        rv = self.get(id)
        if rv is None:
            self._raise_not_exist('id=%s' % id, message)
        return rv

    def one_or_raise(self, message=None):
        try:
            rv = self.one()
        except NoResultFound:
            self._raise_not_exist(self.statement, message)
        except MultipleResultsFound:
            self._raise_multiple_results(self.statement)
        return rv

    def paginator(self, _max, index):
        count = self.with_entities(func.count(self.entity_class.id)).scalar()

        if (index - 1) * _max > count or index <= 0:
            raise ValueError('index or max argument overflow')

        if not count:
            return count, self

        ret = self.offset(_max * (index - 1)).limit(_max)
        return count, ret

    def load_only(self, *args, **kwargs):
        return self.options(load_only(*args, **kwargs))


class TorextDeclarativeMeta(DeclarativeMeta):
    def __new__(cls, name, bases, attrs):
        print('cls cls', cls)
        model_cls = super(TorextDeclarativeMeta, cls).__new__(cls, name, bases, attrs)
        # model_cls = type.__new__(cls, name, bases, attrs)

        exccls_name = '%sDoesNotExist' % name
        exccls_attrs = {'__module__': model_cls.__module__}

        model_cls.DoesNotExist = type(exccls_name, (DoesNotExist, ), exccls_attrs)
        return model_cls


class _Model(object):
    query = None

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class SQLAlchemy(object):
    """
    Usage:

    1. with app
    # database.py
    >>> from torext.sql import SQLAlchemy
    >>> db = SQLAlchemy()

    # app.py
    >>> from myproject.database import db
    >>> db.init_app(app)

    2. without app
    >>> from torext.sql import SQLAlchemy
    >>> db = SQLAlchemy('sqlite://')
    """

    def __init__(self, app=None, uri=None, config=None, session_options=None):
        self._engine = None

        # session is created without an engine,
        # it will be binded with engine later by uri argument
        # or through app settings comes from `init_app` invoking
        self.session = self.create_scoped_session(session_options)

        self.Model = self.make_declarative_base()

        # config
        if app:
            assert isinstance(app, TorextApp), 'app should be an instance of TorextApp'
            self.config = self.init_config(app.settings['SQLALCHEMY'])
        else:
            self.config = self.init_config(config)
        if uri:
            self.config['uri'] = uri

        if self.config['uri']:
            self.session.configure(bind=self.engine)

        self.app = app
        self._include_sqlalchemy()

    def init_app(self, app):
        self.app = app
        self.config = self.init_config(app.settings['SQLALCHEMY'])
        self.session.configure(bind=self.engine)

    def create_scoped_session(self, options=None):
        if options is None:
            options = {}
        return scoped_session(sessionmaker(query_cls=BaseQuery), **options)

    def make_declarative_base(self):
        base = declarative_base(cls=_Model, name='Model', metaclass=TorextDeclarativeMeta)
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

    def init_config(self, incoming=None):
        config = {
            'uri': None,
            'pool_size': None,
            'pool_timeout': None,
            'pool_recycle': None,
            'echo': False,
        }
        if incoming:
            for k in config:
                if k in incoming:
                    config[k] = incoming[k]
        return config

    @property
    def engine(self):
        if not self._engine:
            self._engine = self.get_engine()
        return self._engine

    def get_engine(self):
        assert self.config['uri'], 'uri should not be empty,'\
            ' assign by call init_app or explicitly passing'
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
        logging.info('SQLAlchemy engine config: %s, %s', uri_obj, options)
        engine = sqlalchemy.create_engine(uri_obj, **options)
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
            self.config.get('uri')
        )


# helpers

class MutationObj(Mutable):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, dict) and not isinstance(value, MutationDict):
            return MutationDict.coerce(key, value)
        if isinstance(value, list) and not isinstance(value, MutationList):
            return MutationList.coerce(key, value)
        return value

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        key = attribute.key
        if parent_cls is not attribute.class_:
            return

        # rely on "propagate" here
        parent_cls = attribute.class_

        def load(state, *args):
            val = state.dict.get(key, None)
            if coerce:
                val = cls.coerce(key, val)
                state.dict[key] = val
            if isinstance(val, cls):
                val._parents[state.obj()] = key

        def set(target, value, oldvalue, initiator):
            if not isinstance(value, cls):
                value = cls.coerce(key, value)
            if isinstance(value, cls):
                value._parents[target.obj()] = key
            if isinstance(oldvalue, cls):
                oldvalue._parents.pop(target.obj(), None)
            return value

        def pickle(state, state_dict):
            val = state.dict.get(key, None)
            if isinstance(val, cls):
                if 'ext.mutable.values' not in state_dict:
                    state_dict['ext.mutable.values'] = []
                state_dict['ext.mutable.values'].append(val)

        def unpickle(state, state_dict):
            if 'ext.mutable.values' in state_dict:
                for val in state_dict['ext.mutable.values']:
                    val._parents[state.obj()] = key

        sqlalchemy.event.listen(parent_cls, 'load', load, raw=True, propagate=True)
        sqlalchemy.event.listen(parent_cls, 'refresh', load, raw=True, propagate=True)
        sqlalchemy.event.listen(attribute, 'set', set, raw=True, retval=True, propagate=True)
        sqlalchemy.event.listen(parent_cls, 'pickle', pickle, raw=True, propagate=True)
        sqlalchemy.event.listen(parent_cls, 'unpickle', unpickle, raw=True, propagate=True)


class MutationDict(MutationObj, dict):
    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to MutationDict"""
        self = MutationDict((k,MutationObj.coerce(key, v)) for (k, v) in value.items())
        self._key = key
        return self

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, MutationObj.coerce(self._key, value))
        self.changed()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()


class MutationList(MutationObj, list):
    @classmethod
    def coerce(cls, key, value):
        """Convert plain list to MutationList"""
        self = MutationList((MutationObj.coerce(key, v) for v in value))
        self._key = key
        return self

    def __setitem__(self, idx, value):
        list.__setitem__(self, idx, MutationObj.coerce(self._key, value))
        self.changed()

    def __setslice__(self, start, stop, values):
        list.__setslice__(self, start, stop, (MutationObj.coerce(self._key, v) for v in values))
        self.changed()

    def __delitem__(self, idx):
        list.__delitem__(self, idx)
        self.changed()

    def __delslice__(self, start, stop):
        list.__delslice__(self, start, stop)
        self.changed()

    def append(self, value):
        list.append(self, MutationObj.coerce(self._key, value))
        self.changed()

    def insert(self, idx, value):
        list.insert(self, idx, MutationObj.coerce(self._key, value))
        self.changed()

    def extend(self, values):
        list.extend(self, (MutationObj.coerce(self._key, v) for v in values))
        self.changed()

    def pop(self, *args, **kw):
        value = list.pop(self, *args, **kw)
        self.changed()
        return value

    def remove(self, value):
        list.remove(self, value)
        self.changed()
