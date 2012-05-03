#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from torext import errors
from torext.lib.utils import OneInstanceObject


def configure_conns(options):

    for typ, typ_opts in options.iteritems():

        for label, label_opts in typ_opts.iteritems():
            try:
                func = globals()['connect_' + typ]
            except KeyError:
                raise errors.ConnectionError('Could not connect %s, function unexist' % typ)

            try:
                conn = func(label_opts)
            except Exception, e:
                raise errors.ConnectionError('Set connection %s failed, options: %s, original error: %s' % (typ, label_opts, e))

            conns.set(typ, label, conn)


class Connections(OneInstanceObject):
    """What a connection is, doesn't mean linking with kinda facility,
    like MySQL, MongoDB, RabbitMQ...
    but a certain object that can be mainputated uniquely,
    for example, a session in MySQl, a database of MongoDB,

    Connections combines those up.
    """
    def __init__(self):
        self._container = {}

    def set(self, typ, label, conn):
        if not typ in self._container:
            self._container[typ] = {}
        self._container[typ][label] = conn

    def get(self, typ, name):
        try:
            return self._container[typ][name]
        except KeyError:
            raise errors.ConnectionError('Connection %s:%s not exist' % (typ, name))

    def __str__(self):
        conns_str = ','.join(
            ['%s(%s)' % (i, len(j.keys())) for i, j in self._container.iteritems()])
        return '<Connections: %s >' % conns_str


conns = Connections.instance()


# def connect_rdb():
#     pass


def connect_mongodb(opts):
    """
    opts structure:
    : host
    : port
    : database
    """
    # from mongokit import Connection
    from pymongo import Connection
    conn = Connection(opts['host'], opts['port'])
    # execute this function to ensure succeed
    conn.database_names()
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
