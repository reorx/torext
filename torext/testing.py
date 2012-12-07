#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Application level testing solution

import urllib
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop


#class TestCase(unittest.TestCase):
    #def get_app(self):
        #raise NotImplementedError

    #def setUp(self):
        #self.app = self.get_app()
        #pass

    #def tearDown(self):
        #pass


class TestClient(object):
    def __init__(self, app):
        if app.is_running:
            raise RuntimeError('You should not instance TestClient\
                               when applicaion is running')
        if not app.is_setuped:
            app.setup()

        self.app = app

    def get(self, path, **kwgs):
        return self.request('get', path, **kwgs)

    def post(self, path, data={}, **kwgs):
        body = urllib.urlencode(data)
        return self.request('post', path, body=body, **kwgs)

    def delete(self, path, **kwgs):
        return self.request('delete', path, **kwgs)

    def put(self, path, **kwgs):
        return self.request('put', path, **kwgs)

    def get_protocol(self):
        return 'http'

    def get_http_port(self):
        return self.app.settings['PORT']

    def get_url(self, path):
        """Returns an absolute url for the given path on the test server."""
        return '%s://localhost:%s%s' % (self.get_protocol(),
                                        self.get_http_port(), path)

    def _setup(self):
        # init app.application, app.http_server, app.io_loop
        self.app._init_infrastructures()

        self.http_client = AsyncHTTPClient(io_loop=self.app.io_loop)

    def _teardown(self):
        app = self.app
        # first stop running
        app.io_loop.stop()
        app.io_loop.running = False

        # then do some other cleaning
        if (not IOLoop.initialized() or
                app.io_loop is not IOLoop.instance()):
            # Try to clean up any file descriptors left open in the ioloop.
            # This avoids leaks, especially when tests are run repeatedly
            # in the same process with autoreload (because curl does not
            # set FD_CLOEXEC on its file descriptors)
            app.io_loop.close(all_fds=True)
        app.http_server.stop()

        self.http_client.close()

    def _on_resp(self, resp):
        self.resp = resp
        self._teardown()

    def request(self, method, path, **kwgs):
        self._setup()

        self.http_client.fetch(self.get_url(path),
                               self._on_resp, method=method.upper(), **kwgs)

        self.app.io_loop.start()
        resp, self.resp = self.resp, None
        return resp
