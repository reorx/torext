#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from tornado.options import options
from .utils.format import _json, utf8
from .exceptions import BaseError

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

def connect_mongodb(opts):
    """
    opts structure:
    : host
    : port
    : database
    """
    from pymongo import Connection
    from pymongo import errors
    try:
        _conn = Connection(opts['host'], opts['port'])
    except errors.AutoReconnect:
        return None
    conn = _conn[opts['database']]
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

def connect_redis(opts):
    return None

from .utils.factory import OneInstanceImp
"""
opts structure:
    {
        'mysql': (
        )
    }
"""
class Connections(OneInstanceImp):
    """What a connection is, doesn't mean linking with kinda facility,
    like MySQL, MongoDB, RabbitMQ...
    but a certain object that can be mainputated uniquely,
    for example, a session in MySQl, a database of MongoDB,
    and, as to RabbitMQ, itself fits this concept well enough
    """
    def __init__(self, opts):
        self._availables = {}
        self._options = opts
        for typ in opts:
            for i, j in opts[typ].iteritems():
                self.set(typ, i, j)

        logging.info('connections:: ' +\
            '\n'.join(
                ['%s\t%s' % (i, str(self._availables[i]))\
                    for i in self._availables])
        )

    def set(self, typ, name, opts):
        if not typ in ('mysql', 'mongodb', 'rabbitmq', 'redis'):
            raise ConnectionSetError('Connection type not exist')
        if not opts['enable']:
            return
        conn = globals()['connect_'+typ](opts)
        if conn is None:
            raise ConnectionSetError('Set connection %s error' % typ)
        if typ not in self._availables:
            self._availables[typ] = {}
        self._availables[typ][name] = conn

    def get(self, typ, name):
        try:
            return self._availables[typ][name]
        except KeyError:
            return None

    def reset(self, typ, name):
        del self._availables[typ][name]
        self.set(typ, name, self._options[typ][name])

class ConnectionSetError(BaseError):
    pass

connections = Connections.instance(options.connections)
# TODO start an ioloop to periodly check connections
