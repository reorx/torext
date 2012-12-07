# -*- coding: utf-8 -*-
"""
    flaskext.sqlalchemy
    ~~~~~~~~~~~~~~~~~~~

    Adds basic SQLAlchemy support to your application.

    :copyright: (c) 2012 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement, absolute_import
import re
import sys
import time
import functools
import sqlalchemy
from functools import partial
from operator import itemgetter
from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.interfaces import MapperExtension, SessionExtension, EXT_CONTINUE
from sqlalchemy.interfaces import ConnectionProxy
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

# the best timer function for the platform
if sys.platform == 'win32':
    _timer = time.clock
else:
    _timer = time.time


from flask.signals import Namespace

_signals = Namespace()
models_committed = _signals.signal('models-committed')
before_models_committed = _signals.signal('before-models-committed')


def _make_table(db):
    def _make_table(*args, **kwargs):
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
        info = kwargs.pop('info', None) or {}
        info.setdefault('bind_key', None)
        kwargs['info'] = info
        return sqlalchemy.Table(*args, **kwargs)
    return _make_table


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


def _include_sqlalchemy(obj):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(obj, key):
                setattr(obj, key, getattr(module, key))
    # Note: obj.Table does not attempt to be a SQLAlchemy Table class.
    obj.Table = _make_table(obj)
    obj.mapper = signalling_mapper
    obj.relationship = _wrap_with_default_query_class(obj.relationship)
    obj.relation = _wrap_with_default_query_class(obj.relation)
    obj.dynamic_loader = _wrap_with_default_query_class(obj.dynamic_loader)


class _DebugQueryTuple(tuple):
    statement = property(itemgetter(0))
    parameters = property(itemgetter(1))
    start_time = property(itemgetter(2))
    end_time = property(itemgetter(3))

    @property
    def duration(self):
        return self.end_time - self.start_time

    def __repr__(self):
        return '<query statement="%s" parameters=%r duration=%.03f>' % (
            self.statement,
            self.parameters,
            self.duration
        )


_sqlalchemy_queries = []


class _ConnectionDebugProxy(ConnectionProxy):
    """Helps debugging the database."""

    def cursor_execute(self, execute, cursor, statement, parameters,
                       context, executemany):
        start = _timer()
        try:
            return execute(cursor, statement, parameters, context)
        finally:
            _sqlalchemy_queries.append(
                _DebugQueryTuple((
                    statement, parameters, start, _timer()))
            )


class _SignalTrackingMapperExtension(MapperExtension):

    def after_delete(self, mapper, connection, instance):
        return self._record(mapper, instance, 'delete')

    def after_insert(self, mapper, connection, instance):
        return self._record(mapper, instance, 'insert')

    def after_update(self, mapper, connection, instance):
        return self._record(mapper, instance, 'update')

    def _record(self, mapper, model, operation):
        pk = tuple(mapper.primary_key_from_instance(model))
        orm.object_session(model)._model_changes[pk] = (model, operation)
        return EXT_CONTINUE


class _SignallingSessionExtension(SessionExtension):

    def before_commit(self, session):
        print 'in before_commit'
        d = session._model_changes
        if d:
            print 'send before_commit'
            #before_models_committed.send(session.app, changes=d.values())
        return EXT_CONTINUE

    def after_commit(self, session):
        d = session._model_changes
        if d:
            print 'send after_commit'
            #models_committed.send(session.app, changes=d.values())
            d.clear()
        return EXT_CONTINUE

    def after_rollback(self, session):
        session._model_changes.clear()
        return EXT_CONTINUE


class _SignallingSession(Session):

    def __init__(self, db, autocommit=False, autoflush=False, **options):
        self.sa = db
        self._model_changes = {}
        binds = db.get_binds()
        print '! binds', binds
        Session.__init__(self, autocommit=autocommit, autoflush=autoflush,
                         extension=[_SignallingSessionExtension()],
                         bind=db.engine,
                         binds=binds, **options)

    def get_bind(self, mapper, clause=None):
        # mapper is None if someone tries to just get a connection
        if mapper is not None:
            info = getattr(mapper.mapped_table, 'info', {})
            bind_key = info.get('bind_key')
            if bind_key is not None:
                return self.sa.get_engine(bind=bind_key)
        return Session.get_bind(self, mapper, clause)


class BaseQuery(orm.Query):
    """The default query object used for models, and exposed as
    :attr:`~SQLAlchemy.Query`. This can be subclassed and
    replaced for individual models by setting the :attr:`~Model.query_class`
    attribute.  This is a subclass of a standard SQLAlchemy
    :class:`~sqlalchemy.orm.query.Query` class and has all the methods of a
    standard query as well.
    """
    pass


class _QueryProperty(object):

    def __init__(self, sqlalchemy):
        self.session = sqlalchemy.session

    def __get__(self, model_obj, model_class):
        # NOTE mapper the model before getting query instance
        try:
            mapper = orm.class_mapper(model_class)
            if mapper:
                return model_class.query_class(mapper, session=self.session())
        except UnmappedClassError:
            return None


class _EngineConnector(object):

    def __init__(self, sa, bind=None):
        self._sa = sa
        self._engine = None
        self._connected_for = None
        self._bind = bind

    def get_uri(self):
        if self._bind is None:
            return self._sa.config['SQLALCHEMY_DATABASE_URI']
        binds = self._sa.config.get('SQLALCHEMY_BINDS') or ()
        assert self._bind in binds, \
            'Bind %r is not specified.  Set it in the SQLALCHEMY_BINDS ' \
            'configuration variable' % self._bind
        return binds[self._bind]

    def get_engine(self):
        uri = self.get_uri()
        uri = self._sa.config['SQLALCHEMY_DATABASE_URI']
        echo = self._sa.config['SQLALCHEMY_ECHO']
        if (uri, echo) == self._connected_for:
            return self._engine
        info = make_url(uri)
        options = {'convert_unicode': True}
        self._sa.apply_pool_defaults(options)
        self._sa.apply_driver_hacks(info, options)
        if self._sa.config['SQLALCHEMY_RECORD_QUERIES']:
            options['proxy'] = _ConnectionDebugProxy()
        if echo:
            options['echo'] = True
        self._engine = rv = sqlalchemy.create_engine(info, **options)
        self._connected_for = (uri, echo)
        return rv


def _defines_primary_key(d):
    """Figures out if the given dictonary defines a primary key column."""
    return any(v.primary_key for k, v in d.iteritems()
               if isinstance(v, sqlalchemy.Column))


_camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')


class _BoundDeclarativeMeta(DeclarativeMeta):

    def __new__(cls, name, bases, d):
        tablename = d.get('__tablename__')

        # generate a table name automatically if it's missing and the
        # class dictionary declares a primary key.  We cannot always
        # attach a primary key to support model inheritance that does
        # not use joins.  We also don't want a table name if a whole
        # table is defined
        if not tablename and d.get('__table__') is None and \
                _defines_primary_key(d):
            def _join(match):
                word = match.group()
                if len(word) > 1:
                    return ('_%s_%s' % (word[:-1], word[-1])).lower()
                return '_' + word.lower()
            d['__tablename__'] = _camelcase_re.sub(_join, name).lstrip('_')

        return DeclarativeMeta.__new__(cls, name, bases, d)

    def __init__(self, name, bases, d):
        bind_key = d.pop('__bind_key__', None)
        DeclarativeMeta.__init__(self, name, bases, d)
        if bind_key is not None:
            self.__table__.info['bind_key'] = bind_key


def signalling_mapper(*args, **kwargs):
    """Replacement for mapper that injects some extra extensions"""
    kwargs['extension'] = [_SignalTrackingMapperExtension()]
    return sqlalchemy.orm.mapper(*args, **kwargs)


class Model(object):
    """Baseclass for custom user models."""
    #: the query class used.  The :attr:`query` attribute is an instance
    #: of this class.  By default a :class:`BaseQuery` is used.
    query_class = BaseQuery

    #: an instance of :attr:`query_class`.  Can be used to query the
    #: database for instances of this model.
    query = None


class SQLAlchemy(object):

    def __init__(self, use_native_unicode=True, session_options={}):
        self.use_native_unicode = use_native_unicode
        self.session = self.create_scoped_session(session_options)

        self.Model = self.make_declarative_base()

        _include_sqlalchemy(self)
        #self.Query = BaseQuery

        self.config = {}

        # NOTE store the binded connectors
        self.connectors = {}

        self.init()
        self.Query = BaseQuery

        # NOTE engine is still not created now

    @property
    def metadata(self):
        """Returns the metadata"""
        return self.Model.metadata

    def create_scoped_session(self, options=None):
        """Helper factory method that creates a scoped session."""
        if options is None:
            options = {}
        # NOTE Session can be controled
        return orm.scoped_session(
            partial(_SignallingSession, self, **options)
        )

    def make_declarative_base(self):
        """Creates the declarative base."""
        base = declarative_base(cls=Model, name='Model',
                                mapper=signalling_mapper,
                                metaclass=_BoundDeclarativeMeta)
        base.query = _QueryProperty(self)
        return base

    def init(self):
        """This callback can be used to initialize an application for the
        use with this database setup.  Never use a database in the context
        of an application not initialized that way or connections will
        leak.
        """
        self.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite://')
        self.config.setdefault('SQLALCHEMY_BINDS', None)
        self.config.setdefault('SQLALCHEMY_NATIVE_UNICODE', None)
        self.config.setdefault('SQLALCHEMY_ECHO', False)
        self.config.setdefault('SQLALCHEMY_RECORD_QUERIES', None)
        self.config.setdefault('SQLALCHEMY_POOL_SIZE', None)
        self.config.setdefault('SQLALCHEMY_POOL_TIMEOUT', None)
        self.config.setdefault('SQLALCHEMY_POOL_RECYCLE', None)

        # NOTE Flask want's to make the session being removed after the request
        # using self.session.remove()

    def apply_pool_defaults(self, options):
        """ Modify options dict
        """
        def _setdefault(optionkey, configkey):
            value = self.config[configkey]
            if value is not None:
                options[optionkey] = value
        _setdefault('pool_size', 'SQLALCHEMY_POOL_SIZE')
        _setdefault('pool_timeout', 'SQLALCHEMY_POOL_TIMEOUT')
        _setdefault('pool_recycle', 'SQLALCHEMY_POOL_RECYCLE')

    def apply_driver_hacks(self, info, options):
        """This method is called before engine creation and used to inject
        driver specific hacks into the options.  The `options` parameter is
        a dictionary of keyword arguments that will then be used to call
        the :func:`sqlalchemy.create_engine` function.

        The default implementation provides some saner defaults for things
        like pool sizes for MySQL and sqlite.  Also it injects the setting of
        `SQLALCHEMY_NATIVE_UNICODE`.
        """
        if info.drivername == 'mysql':
            info.query.setdefault('charset', 'utf8')
            options.setdefault('pool_size', 10)
            options.setdefault('pool_recycle', 7200)
        elif info.drivername == 'sqlite':
            pool_size = options.get('pool_size')
            detected_in_memory = False
            # we go to memory and the pool size was explicitly set to 0
            # which is fail.  Let the user know that
            if info.database in (None, '', ':memory:'):
                detected_in_memory = True
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

            if detected_in_memory:
                pass
            # if it's not an in memory database we make the path absolute.
            #if not detected_in_memory:
                #info.database = os.path.join(app.root_path, info.database)

        unu = self.config['SQLALCHEMY_NATIVE_UNICODE']
        if unu is None:
            unu = self.use_native_unicode
        if not unu:
            options['use_native_unicode'] = False

    @property
    def engine(self):
        return self.get_engine()

    def get_engine(self, bind=None):
        """Returns a specific engine.
        """
        connector = self.connectors.get(bind)
        if connector is None:
            connector = _EngineConnector(self, bind)
            self.connectors[bind] = connector
        return connector.get_engine()

    def get_tables_for_bind(self, bind=None):
        """Returns a list of all tables relevant for a bind."""
        result = []
        for table in self.Model.metadata.tables.itervalues():
            if table.info.get('bind_key') == bind:
                result.append(table)
        return result

    def get_binds(self):
        """Returns a dictionary with a table->engine mapping.

        This is suitable for use of sessionmaker(binds=db.get_binds()).
        """
        binds = [None] + list(self.config.get('SQLALCHEMY_BINDS') or ())
        retval = {}
        for bind in binds:
            engine = self.get_engine(bind)
            tables = self.get_tables_for_bind(bind)
            retval.update(dict((table, engine) for table in tables))
        return retval

    def _execute_for_all_tables(self, bind, operation):

        if bind == '__all__':
            binds = [None] + list(self.config.get('SQLALCHEMY_BINDS') or ())
        elif isinstance(bind, basestring):
            binds = [bind]
        else:
            binds = bind

        for bind in binds:
            tables = self.get_tables_for_bind(bind)
            op = getattr(self.Model.metadata, operation)
            op(bind=self.get_engine(bind), tables=tables)

    def create_all(self, bind='__all__'):
        """Creates all tables.

        .. versionchanged:: 0.12
           Parameters were added
        """
        self._execute_for_all_tables(bind, 'create_all')

    def drop_all(self, bind='__all__'):
        """Drops all tables.

        .. versionchanged:: 0.12
           Parameters were added
        """
        self._execute_for_all_tables(bind, 'drop_all')

    def reflect(self, bind='__all__'):
        """Reflects tables from the database.

        .. versionchanged:: 0.12
           Parameters were added
        """
        self._execute_for_all_tables(bind, 'reflect')

    def __repr__(self):
        return '<%s engine=%r>' % (
            self.__class__.__name__,
            self.config['SQLALCHEMY_DATABASE_URI']
        )
