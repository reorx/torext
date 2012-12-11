#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jsonrpclib import Server
from torext.app import TorextApp
from torext.handlers.rpc import JSONRPCHandler


def func_add(x, y):
    return x + y


app = TorextApp()


@app.route('/rpc')
class RPCHdr(JSONRPCHandler):
    def add(self, *args, **kwgs):
        return func_add(*args, **kwgs)

    def obj(self):
        return self


class RPCTest(app.TestCase):
    def setUp(self):
        super(RPCTest, self).setUp()
        self.rpc = Server(self.c.get_url('/rpc'))

    def test_add(self):
        args = (1, 2)
        assert func_add(*args) == self.rpc.add(*args)
