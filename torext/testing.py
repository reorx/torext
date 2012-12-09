#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Application level testing solution
#
# it should make testing easy as a shit

import sys
import time
import urllib
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado.util import raise_exc_info
from tornado.stack_context import NullContext
from tornado import web


class TestClient(object):
    def __init__(self, app):
        if app.is_running:
            raise RuntimeError('You should not instance TestClient\
                               when applicaion is running')

        # start::tornado.testing.AsyncTestCase
        self.__stopped = False
        self.__running = False
        self.__failure = None
        self.__stop_args = None
        self.__timeout = None
        # end::tornado.testing.AsyncTestCase

        self._handler_exc_info = None

        app.update_settings({
            'TESTING': True
        })

        self.app = app

        # redo setup disregard whether it has been setuped or not
        app.setup()

    def _setup(self):
        # start::tornado.testing.AsyncTestCase
        self.io_loop = self.get_new_ioloop()
        # end::tornado.testing.AsyncTestCase

        self.app.io_loop = self.io_loop
        # init app.application and app.http_server
        self.app._init_infrastructures()

        self.patch_app_handlers()

        self.http_server = self.app.http_server
        self.http_client = AsyncHTTPClient(io_loop=self.io_loop)

    def _teardown(self):
        # start::tornado.testing.AsyncHTTPTestCase
        self.http_server.stop()
        if (not IOLoop.initialized() or
                self.http_client.io_loop is not IOLoop.instance()):
            self.http_client.close()
        # end::tornado.testing.AsyncHTTPTestCase

        # start::tornado.testing.AsyncTestCase
        if (not IOLoop.initialized() or
                self.io_loop is not IOLoop.instance()):
            # Try to clean up any file descriptors left open in the ioloop.
            # This avoids leaks, especially when tests are run repeatedly
            # in the same process with autoreload (because curl does not
            # set FD_CLOEXEC on its file descriptors)
            self.io_loop.close(all_fds=True)
        # end::tornado.testing.AsyncTestCase

    def request(self, method, path, **kwgs):
        self._setup()

        kwgs['method'] = method.upper()

        try:
            self.http_client.fetch(self.get_url(path), self.stop, **kwgs)
            resp = self.wait()
        finally:
            self._teardown()

        #resp, self.resp = self.resp, None
        return resp

    def stop(self, _arg=None, **kwargs):
        '''Stops the ioloop, causing one pending (or future) call to wait()
        to return.

        Keyword arguments or a single positional argument passed to stop() are
        saved and will be returned by wait().
        '''
        assert _arg is None or not kwargs
        self.__stop_args = kwargs or _arg
        if self.__running:
            self.io_loop.stop()
            self.__running = False
        self.__stopped = True

    def wait(self, condition=None, timeout=5):
        """Runs the IOLoop until stop is called or timeout has passed.

        In the event of a timeout, an exception will be thrown.

        If condition is not None, the IOLoop will be restarted after stop()
        until condition() returns true.
        """
        if not self.__stopped:
            if timeout:
                def timeout_func():
                    try:
                        raise self.failureException(
                            'Async operation timed out after %s seconds' %
                            timeout)
                    except Exception:
                        self.__failure = sys.exc_info()
                    self.stop()
                if self.__timeout is not None:
                    self.io_loop.remove_timeout(self.__timeout)
                self.__timeout = self.io_loop.add_timeout(time.time() + timeout, timeout_func)
            while True:
                self.__running = True
                with NullContext():
                    # Wipe out the StackContext that was established in
                    # self.run() so that all callbacks executed inside the
                    # IOLoop will re-run it.
                    self.io_loop.start()
                if (self.__failure is not None or
                        condition is None or condition()):
                    break
        assert self.__stopped
        self.__stopped = False
        self.__rethrow()
        result = self.__stop_args
        self.__stop_args = None
        return result

    def get_new_ioloop(self):
        '''Creates a new IOLoop for this test.  May be overridden in
        subclasses for tests that require a specific IOLoop (usually
        the singleton).
        '''
        return IOLoop()

    def __rethrow(self):
        if self.__failure is not None:
            failure = self.__failure
            self.__failure = None
            raise_exc_info(failure)

    def get(self, path, data={}, **kwgs):
        if data:
            path = '%s?%s' % (path, urllib.urlencode(data))
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

    def handler_exc(self):
        if self._handler_exc_info:
            raise_exc_info(self._handler_exc_info)

    def patch_handler(self, hdr):
        if not isinstance(hdr, web.StaticFileHandler):
            hdr._testing_app_client = self
            hdr._handle_request_exception = _handle_request_exception

    def patch_app_handlers(self):
        for host_pattern, rules in self.app.application.handlers:
            for r in rules:
                self.patch_handler(r.handler_class)


def _handle_request_exception(self, e):
    import sys
    import httplib
    import logging
    from tornado.web import HTTPError

    if isinstance(e, HTTPError):
        if e.log_message:
            format = "%d %s: " + e.log_message
            args = [e.status_code, self._request_summary()] + list(e.args)
            logging.warning(format, *args)
        if e.status_code not in httplib.responses:
            logging.error("Bad HTTP status code: %d", e.status_code)
            self.send_error(500, exc_info=sys.exc_info())
        else:
            self.send_error(e.status_code, exc_info=sys.exc_info())
    else:
        self._testing_app_client._handler_exc_info = sys.exc_info()

        logging.error("Uncaught exception %s\n%r", self._request_summary(),
                      self.request, exc_info=True)
        self.send_error(500, exc_info=sys.exc_info())
