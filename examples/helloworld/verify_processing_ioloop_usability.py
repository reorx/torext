#!/usr/bin/env python
# -*- coding: utf-8 -*-


from multiprocessing import Process
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        self.write("Hello, world post")


io_loop = tornado.ioloop.IOLoop.instance()

application = tornado.web.Application([
    (r"/", MainHandler),
])
http_server = tornado.httpserver.HTTPServer(application)
http_server.listen(options.port)


process = Process(target=io_loop.start)
process.start()
print 'process starts'
