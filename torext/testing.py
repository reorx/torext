#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Application level testing solution
#
# it should make testing easy as shit

import sys
import time
import urllib
import unittest
import logging
import mimetypes
from Cookie import SimpleCookie
from urllib import quote
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado.stack_context import NullContext
from tornado.escape import json_encode
from tornado import web

from torext.utils import raise_exc_info


COOKIE_HEADER_KEY = 'Set-Cookie'


# The one variable and two functions below are copied from
# requests HTTP library <http://python-requests.org>.
# :copyright: (c) 2013 by Kenneth Reitz.
# :license: Apache 2.0, see LICENSE for more details.

# The unreserved URI characters (RFC 3986)
UNRESERVED_SET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    + "0123456789-._~")


def unquote_unreserved(uri):
    """Un-escape any percent-escape sequences in a URI that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.
    """
    parts = uri.split('%')
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            c = chr(int(h, 16))
            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = '%' + parts[i]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote_uri(uri):
    """Re-quote the given URI.

    This function passes the given URI through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.
    """
    # Unquote only the unreserved characters
    # Then quote only illegal characters (do not quote reserved, unreserved,
    # or '%')
    return quote(unquote_unreserved(uri), safe="!#$%&'()*+,/:;=?@[]~")


class TestClient(object):
    def __init__(self, app, raise_handler_exc=False):
        # TODO add `host` kwarg
        if app.is_running:
            raise RuntimeError('You should not instance TestClient\
                               when applicaion is running')

        self.raise_handler_exc = raise_handler_exc

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
        # redo setup to make settings changes effective
        app.setup()

        self.app = app
        self.setup()

    def setup(self):
        """Setup facilities for running the server

        NOTE if you get all "Address already in use" error except the first one,
        the bug may well happened in this function.
        """
        # start::tornado.testing.AsyncTestCase
        #self.io_loop = self.get_new_ioloop()
        # end::tornado.testing.AsyncTestCase
        #self.app.io_loop = self.io_loop

        # init app.io_loop, app.application and app.http_server
        self.app._init_infrastructures()
        self.io_loop = self.app.io_loop

        if self.raise_handler_exc:
            self.patch_app_handlers()

        self.http_server = self.app.http_server
        self.http_client = AsyncHTTPClient(io_loop=self.io_loop)

    def close(self):
        """CLose http_server, io_loop by sequence, to ensure the environment
        is cleaned up and invoking `setup` successfully within next test function

        It is suggested to be called in `TestCase.tearDown`
        """
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

    def _parse_cookies(self, resp):
        if COOKIE_HEADER_KEY in resp.headers:
            c = SimpleCookie(resp.headers.get(COOKIE_HEADER_KEY))
        elif COOKIE_HEADER_KEY.lower() in resp.headers:
            c = SimpleCookie(resp.headers.get(COOKIE_HEADER_KEY.lower()))
        else:
            c = None
        resp.cookies = c

    def _add_cookies(self, cookies, kwgs):
        # SimpleCookie is inherited from dict, so judge it first
        if isinstance(cookies, SimpleCookie):
            c = cookies
        elif isinstance(cookies, dict):
            c = SimpleCookie()
            for k, v in cookies.iteritems():
                c[k] = v
        else:
            raise TypeError('cookies kwarg should be dict or SimpleCookie instance')

        if 'headers' in kwgs:
            headers = kwgs['headers']
        else:
            headers = kwgs['headers'] = {}

        headers['Cookie'] = c.output().lstrip(COOKIE_HEADER_KEY + ': ')
        #print 'headers', headers

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

    def __rethrow(self):
        if self.__failure is not None:
            failure = self.__failure
            self.__failure = None
            raise_exc_info(failure)

    def request(self, method, path,
                data=None, json=False,
                files=None,
                cookies=None, **kwgs):

        kwgs['method'] = method

        # `path` should be utf-8 encoded string to complete requote process
        if isinstance(path, unicode):
            path = path.encode('utf8')
        path = requote_uri(path)

        # `body` must be passed if method is one of those three
        if method in ['POST', 'PUT', 'PATCH']:
            headers = kwgs.setdefault('headers', {})
            body = ''
            if files:
                boundary = '1234567890'
                headers['Content-Type'] = 'multipart/form-data; boundary=%s' % boundary
                L = []
                if data:
                    for k, v in data.iteritems():
                        L.append('--' + boundary)
                        L.append('Content-Disposition: form-data; name="%s"' % k)
                        L.append('')
                        L.append(v)
                for k, f in files.iteritems():
                    L.append('--' + boundary)
                    L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (k, f[0]))
                    L.append('Content-Type: %s' % mimetypes.guess_type(f[0])[0] or 'application/octet-stream')
                    L.append('')
                    L.append(f[1])
                L.append('--%s--' % boundary)
                L.append('')
                body = '\r\n'.join(L)
            else:
                if data:
                    if json:
                        body = json_encode(data)
                        headers['Content-Type'] = 'application/json'
                    else:
                        headers['Content-Type'] = 'application/x-www-form-urlencoded'
                        body = urllib.urlencode(data)
            kwgs['body'] = body
        else:
            if data:
                path = '%s?%s' % (path, urllib.urlencode(data))

        if cookies:
            self._add_cookies(cookies, kwgs)

        #print 'fetch kwgs', kwgs
        url = self.get_url(path)
        logging.debug('testing fetch url: %s', url)
        self.http_client.fetch(url, self.stop, **kwgs)
        resp = self.wait()

        self._parse_cookies(resp)

        return resp

    def get(self, *args, **kwgs):
        return self.request('GET', *args, **kwgs)

    def delete(self, *args, **kwgs):
        return self.request('DELETE', *args, **kwgs)

    def post(self, *args, **kwgs):
        return self.request('POST', *args, **kwgs)

    def put(self, *args, **kwgs):
        return self.request('PUT', *args, **kwgs)

    def patch(self, *args, **kwgs):
        return self.request('PATCH', *args, **kwgs)

    def get_protocol(self):
        return 'http'

    def get_http_port(self):
        return self.app.settings['PORT']

    def get_url(self, path):
        """Returns an absolute url for the given path on the test server."""
        return '%s://localhost:%s%s' % (self.get_protocol(),
                                        self.get_http_port(), path)

    def get_handler_exc(self):
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


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.c = self.get_client()

    def tearDown(self):
        self.c.close()

    def get_client(self):
        raise NotImplementedError
