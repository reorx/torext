#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO try..except shouldnt be in connect_$ functions
# TODO function ping_mysql
# TODO function ping_rabbitmq
# TODO in order to ensure connection is properly established, call ping_$ after first connecting

# NOTE 如果connections 在 torext.db中，那么不应包含非db连接如rabbitmq ?
#

import logging
from torext.utils.factory import OneInstanceImp
from torext.errors import ConnectionError


class Connections(OneInstanceImp):
    """What a connection is, doesn't mean linking with kinda facility,
    like MySQL, MongoDB, RabbitMQ...
    but a certain object that can be mainputated uniquely,
    for example, a session in MySQl, a database of MongoDB,
    and, as to RabbitMQ, itself fits this concept well enough.

    Connections combine those up.
    """
    def __init__(self, opts={}):
        """
        if opts is an empty dict, or is not passed, this indicates that
        the configuration will be done in certain service.
        """
        self.opts = opts
        self.configure(opts)

    def configure(self, opts):
        self._availables = {}
        for facility in opts:
            for ider, args in opts[facility].iteritems():
                self.set(facility, ider, args)

    def set(self, typ, name, conn_opts):
        try:
            func = globals()['connect_' + typ]
        except KeyError:
            raise ConnectionError('Connection type not exist')
        if not conn_opts['enable']:
            return
        try:
            conn = func(conn_opts)
        except Exception, e:
            raise ConnectionError('Set connection %s failed, original error: %s' % (typ, e))
        if not typ in self._availables:
            self._availables[typ] = {}
        self._availables[typ][name] = conn

    def get(self, typ, name):
        try:
            return self._availables[typ][name]
        except KeyError:
            raise ConnectionError('Connection %s:%s not exist' % (typ, name))

    def reset(self, typ, name):
        del self._availables[typ][name]
        self.set(typ, name, self.opts[typ][name])

    def __str__(self):
        conns_str = ' '.join(['%s(%s)' % (i, len(self._availables[i].keys()))\
                        for i in self._availables])
        return '<torext.connections.Connections: ' + conns_str + '>'


class MySQLConnection(object):
    def __init__(self, e, s):
        self.engine = e
        self.session = s
        self.check_connection()

    def check_connection(self):
        self.engine.connect()


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
    return conn


def connect_mongodb(opts):
    """
    opts structure:
    : host
    : port
    : database
    """
    from mongokit import Connection
    conn = Connection(opts['host'], opts['port'])
    # execute this function to ensure succeed
    conn.database_names()
    return conn


# # deprecated
# class RabbitMQConnection(object):
#     def __init__(self, _conn, queues):
#         # this is the real connection, but we see itself as the connection
#         self._conn = _conn
#         self.channel = self._conn.channel()
#         self.declared_queues = []
#         for i in queues:
#             self.channel.queue_declare(queue=i)
#             self.declared_queues.append(i)

#     def push(self, queue, msg):
#         queue = utf8(queue)
#         logging.info('push to queue: %s' % queue)
#         if not queue in self.declared_queues:
#             self.channel.queue_declare(queue=queue)
#         if isinstance(msg, (dict, list)):
#             msg = _json(msg)
#         self.channel.basic_publish(routing_key=utf8(queue),
#                                    body=msg,
#                                    exchange='')


def connect_rabbitmq(opts):
    from pika import BlockingConnection, ConnectionParameters
    from pika import PlainCredentials
    cred = PlainCredentials(opts['username'], opts['password'])
    params = ConnectionParameters(host=opts['host'],
                                  port=opts['port'],
                                  virtual_host=opts['virtual_host'],
                                  credentials=cred)
    conn = BlockingConnection(params)
    return conn


def connect_redis(opts):
    import redis
    if opts['use_socket']:
        conn = redis.Redis(unix_socket_path=opts['socket_path'])
    else:
        pool = redis.ConnectionPool(host=opts['host'], port=opts['port'], db=0)
        conn = redis.Redis(connection_pool=pool)
    # get empty string key to ensure succeed
    conn.get('')
    return conn


def connect_rpc(opts):
    """
    Unfortunately, there is no common way to check rpc server connection,
    projects that use torext should do this manually if nesessary.
    """
    from jsonrpclib import Server
    conn_path = '{protocol}://{host}:{port}'.format(**opts)
    conn = Server(conn_path)
    return conn


connections = Connections.instance()
