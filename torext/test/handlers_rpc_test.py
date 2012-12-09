#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from tornado.testing import AsyncHTTPTestCase
from torext.testing import _TestCase
from jsonrpclib import Server
from tornado.web import Application
from torext.handlers.rpc import JSONRPCHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from multiprocessing import Process


_next_port = 59000


def get_unused_port():
    """Returns a (hopefully) unused port number."""
    global _next_port
    port = _next_port
    _next_port = _next_port + 1
    return port


def func_add(x, y):
    return x + y


class RPCHdr(JSONRPCHandler):
    def add(self, *args, **kwgs):
        return func_add(*args, **kwgs)

    def obj(self):
        return self


class JSONRPCTest(_TestCase):
    def setUp(self):
        self._http_server = HTTPServer(Application([(r'/rpc', RPCHdr)]))
        self._port = get_unused_port()
        self._http_server.listen(self._port)

        self._io_loop = IOLoop.instance()

        self.rpc = Server('http://127.0.0.1:%s/rpc' % self._port)

        self.process = Process(target=self._io_loop.start)
        self.process.start()
        self.log.quiet('process started')

    def test_add(self):
        args = (1, 2)
        res = self.rpc.add(*args)
        self.log.quiet('rpc result: %s' % res)
        self.assertEqual(func_add(*args), res)

    def test_bad_return(self):
        self.assertRaises(Exception, self.rpc.obj)

    def tearDown(self):
        self.process.terminate()
        self.log.quiet('process terminated')
