import sys
from torext.handlers.rpc import start_server
from torext.handlers.rpc import BaseRPCHandler


def start_server(handlers, route=r'/', port=8080):
    """
    This is just a friendly wrapper around the default
    Tornado instantiation calls. It simplifies the imports
    and setup calls you'd make otherwise.
    USAGE:
        start_server(handler_class, route=r'/', port=8181)
    """
    if type(handlers) not in (types.ListType, types.TupleType):
        handler = handlers
        handlers = [(route, handler), ]
        if route != '/RPC2':
            # friendly addition for /RPC2 if it's the only one
            handlers.append(('/RPC2', handler))
    application = tornado.web.Application(handlers)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    loop_instance = tornado.ioloop.IOLoop.instance()
    """ Setting the '_server' attribute if not set """
    for (route, handler) in handlers:
        try:
            server_attrib = setattr(handler, '_server', loop_instance)
        except AttributeError:
            handler._server = loop_instance
    loop_instance.start()
    return loop_instance


class TestMethodTree(object):
    def power(self, x, y=2):
        return pow(x, y)

    @private
    def private(self):
        # Shouldn't be called
        return False


class TestRPCHandler(BaseRPCHandler):

    _RPC_ = None

    def add(self, x, y):
        return x+y

    def ping(self, x):
        return x

    def noargs(self):
        return 'Works!'

    tree = TestMethodTree()

    def _private(self):
        # Shouldn't be called
        return False

    @private
    def private(self):
        # Also shouldn't be called
        return False


class TestJSONRPC(TestRPCHandler):
    _RPC_ = JSONRPCParser(JSONRPCLibraryWrapper)

port = 8181
if len(sys.argv) > 1:
    port = int(sys.argv[1])

print 'Starting server on port %s' % port
start_server(TestJSONRPC, port=port)
