#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import threading


class ThreadWorker(threading.Thread):
    def __init__(self, task_fn):
        self.task_fn = task_fn
        super(ThreadWorker, self).__init__()

    def run(self, *args, **kwgs):
        logging.debug('worker:: start..')
        self.task_fn(*args, **kwgs)
        logging.debug('worker:: done..')


def do_task(task_fn, *args, **kwgs):
    logging.debug('task:: init %s' % repr(task_fn))
    ThreadWorker(task_fn).start(*args, **kwgs)


##################################################
# borrow from django.utils.functional.LazyObject #
##################################################

class DummyObject(object):
    """
    A wrapper for reading attributes from another object instantly (no delay)
    """
    def __init__(self, entity):
        # TODO 'if self._entity is None, then..' this way can be improved
        self._entity = self._init_entity(entity)
        if self._entity is None:
            raise ValueError('_entity of DummyObject should not be None')

    def __getattr__(self, name):
        return getattr(self._entity, name)

    def __setattr__(self, name, value):
        if name == "_entity":
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__["_entity"] = value
        else:
            setattr(self._entity, name, value)

    def __delattr__(self, name):
        if name == "_entity":
            raise TypeError("can't delete _entity.")
        delattr(self._entity, name)

    def _init_entity(self):
        """
        Must be implemented by subclasses to initialise the wrapped object.

        return the entity to be used
        """
        raise NotImplementedError

    # introspection support: (is that useful ?)
    # __members__ = property(lambda self: self.__dir__())

    def __dir__(self):
        return  dir(self._entity)


# connections.py

class Connections(OneInstanceImp):
    """What a connection is, doesn't mean linking with kinda facility,
    like MySQL, MongoDB, RabbitMQ...
    but a certain object that can be mainputated uniquely,
    for example, a session in MySQl, a database of MongoDB,
    and, as to RabbitMQ, itself fits this concept well enough.

    Connections combine those up.
    """
    def __init__(self):
        self._availables = {}
        opts = options.connections
        for facility in opts:
            for ider, args in opts[facility].iteritems():
                self.set(facility, ider, args)

        logging.info('-> Connections\n' +
            ''.join(
                ['| {0:<15}| {1:<15}\n'.format(i, repr(self._availables[i]))\
                    for i in self._availables])
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
            # try:
            #     logging.info('check connection {0} - {1}'.format(facility, name))
            #     globals()['ping_' + facility](conn)
            # except ConnectionError, e:
            #     logging.error('%s - %s lost connection: %s' %\
            #         (facility, name, repr(e)))
            # see the error as cretical, raise and crash the application
            logging.info('check connection {0} - {1}'.format(facility, name))
            globals()['ping_' + facility](conn)
    # TODO try reconnect if lost connection

_KEEPER = PeriodicCallback(keep_connections, options.connection_keep_time)
_KEEPER.start()




def ping_rpc(self):
    import socket
    import xmlrpclib
    import jsonrpclib.jsonrpc
    try:
        self.test('test')
    except jsonrpclib.jsonrpc.ProtocolError:
        try:
            self.checkin('test')
        except (socket.error, socket.gaierror, xmlrpclib.ProtocolError) as e:
            raise ConnectionError(repr(e))
        except Exception, e:
            logging.warning('rpc checking unsuccess: ' + repr(e))



def ping_redis(self):
    from redis.exceptions import ConnectionError as RedisConnectionError
    try:
        self.get('KEEPER')
    except RedisConnectionError, e:
        raise ConnectionError(repr(e))



def ping_mongodb(self):
    from pymongo.errors import AutoReconnect
    try:
        self.database_names()
    except AutoReconnect, e:
        raise ConnectionError(repr(e))
