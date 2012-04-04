"""
connect_$facility is designed to be silence debug,
that is, if the attmpt to connect the certain facility failed,
the function will return None instead of raising exceptions
"""


class MySQLConnection(object):
    def __init__(self, e, s):
        self.engine = e
        self.session = s
        self.check_connection()

    def check_connection(self):
        self.engine.connect()


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

# deprecated
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
    from pika import BlockingConnection, ConnectionParameters
    from pika import PlainCredentials
    cred = PlainCredentials(opts['username'], opts['password'])
    params = ConnectionParameters(host=opts['host'],
                                  port=opts['port'],
                                  virtual_host=opts['virtual_host'],
                                  credentials=cred)
    conn = BlockingConnection(params)
    return conn

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
