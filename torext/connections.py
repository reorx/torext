#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO try..except shouldnt be in connect_$ functions
# TODO function ping_mysql
# TODO function ping_rabbitmq
# TODO in order to ensure connection is properly established, call ping_$ after first connecting

import logging
import types

from tornado.options import options
from tornado.ioloop import PeriodicCallback
from .utils.format import _json, utf8
from .utils.factory import OneInstanceImp
from .errors import ConnectionError


class MySQLConnection(object):
    def __init__(self, e, s):
        self.engine = e
        self.session = s

    def check_connection(self):
        from sqlalchemy import exc
        try:
            self.engine.connect()
            return True
        except exc.OperationalError:
            return False

    def keep_connection(self):
        pass


"""
connect_$facility is designed to be silence debug,
that is, if the attmpt to connect the certain facility failed,
the function will return None instead of raising exceptions
"""


def connect_mysql(opts):
    """Receive a SDict instance, return session as `db`, which can represent `connection`
    opts structure::
    : username
    : password
    : host
    : port
    : database
    : debug
    : pool_recycle
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    conn_url = 'mysql+mysqldb://{username}:{password}@{host}:{port}/{database}'.format(**opts)
    engine = create_engine(conn_url,
                           convert_unicode=True,
                           echo=opts['debug'],
                           pool_recycle=opts['pool_recycle'])
    session = scoped_session(sessionmaker(bind=engine))
    conn = MySQLConnection(engine, session)
    if conn.check_connection():
        return conn
    else:
        return None


def ping_mongodb(self):
    from pymongo.errors import AutoReconnect
    try:
        self.database_names()
    except AutoReconnect, e:
        raise ConnectionError(repr(e))


def connect_mongodb(opts):
    """
    opts structure:
    : host
    : port
    : database
    """
    from mongokit import Connection
    conn = Connection(opts['host'], opts['port'])
    # bind method to conn instance
    _ping_connection = ping_mongodb
    types.MethodType(_ping_connection, conn)
    return conn


class RabbitMQConnection(object):
    def __init__(self, _conn, queues):
        # this is the real connection, but we see itself as the connection
        self._conn = _conn
        self.channel = self._conn.channel()
        self.declared_queues = []
        for i in queues:
            self.channel.queue_declare(queue=i)
            self.declared_queues.append(i)

    def push(self, queue, msg):
        queue = utf8(queue)
        logging.info('push to queue: %s' % queue)
        if not queue in self.declared_queues:
            self.channel.queue_declare(queue=queue)
        if isinstance(msg, (dict, list)):
            msg = _json(msg)
        self.channel.basic_publish(routing_key=utf8(queue),
                                   body=msg,
                                   exchange='')


def connect_rabbitmq(opts):
    import socket
    from pika import BlockingConnection, ConnectionParameters
    from pika import PlainCredentials
    cred = PlainCredentials(opts['username'], opts['password'])
    params = ConnectionParameters(host=opts['host'],
                                  port=opts['port'],
                                  virtual_host=opts['virtual_host'],
                                  credentials=cred)
    try:
        _conn = BlockingConnection(params)
    except (socket.gaierror, socket.error):
        return None
    conn = RabbitMQConnection(_conn, opts['queues'])
    return conn


def ping_redis(self):
    from redis.exceptions import ConnectionError
    try:
        self.get('KEEPER')
    except ConnectionError, e:
        global ConnectionError
        raise ConnectionError(repr(e))


def connect_redis(opts):
    import redis
    if opts['use_socket']:
        conn = redis.Redis(unix_socket_path=opts['socket_path'])
    else:
        pool = redis.ConnectionPool(host=opts['host'], port=opts['port'], db=0)
        conn = redis.Redis(connection_pool=pool)
    # bind method to conn instance
    _ping_connection = ping_redis
    types.MethodType(_ping_connection, conn)
    return conn


def ping_rpc(self):
    from socket import error as socket_error
    try:
        self.test('test')
    except socket_error, e:
        raise ConnectionError(repr(e))


def connect_rpc(opts):
    from jsonrpclib import Server
    conn_path = '{protocol}://{host}:{port}'.format(**opts)
    conn = Server(conn_path)
    return conn


class Connections(OneInstanceImp):
    """What a connection is, doesn't mean linking with kinda facility,
    like MySQL, MongoDB, RabbitMQ...
    but a certain object that can be mainputated uniquely,
    for example, a session in MySQl, a database of MongoDB,
    and, as to RabbitMQ, itself fits this concept well enough
    """
    def __init__(self):
        self._availables = {}
        opts = options.connections
        for facility in opts:
            for ider, args in opts[facility].iteritems():
                self.set(facility, ider, args)

        logging.info('connections::\n' +
            ''.join(
                ['%s\t%s\n' % (i, repr(self._availables[i])) for i in self._availables])
        )

    def set(self, typ, name, opts):
        try:
            func = globals()['connect_' + typ]
        except KeyError:
            raise ConnectionError('Connection type not exist')
        if not opts['enable']:
            return
        conn = func(opts)
        if conn is None:
            raise ConnectionError('Set connection %s error' % typ)
        if not typ in self._availables:
            self._availables[typ] = {}
        self._availables[typ][name] = conn

    def get(self, typ, name):
        try:
            return self._availables[typ][name]
        except KeyError:
            return None

    def reset(self, typ, name):
        del self._availables[typ][name]
        self.set(typ, name, options.connections[typ][name])

connections = Connections.instance()


def keep_connections():
    for facility, connMap in connections._availables.iteritems():
        for name, conn in connMap.iteritems():
            try:
                logging.info('check connection {0} - {1}'.format(facility, name))
                globals()['ping_' + facility](conn)
            except ConnectionError, e:
                logging.error('%s - %s lost connection: %s' %\
                    (facility, name, repr(e)))
    # TODO try reconnect if lost connection

_KEEPER = PeriodicCallback(keep_connections, options.connection_keep_time)
_KEEPER.start()
