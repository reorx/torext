#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import email.utils
import hashlib
import mimetypes
import os.path
import stat
import time

import tornado.web
import tornado.locale
from tornado.web import HTTPError
from tornado.escape import utf8

from torext import settings, errors
from torext.log import app_log
from torext.app import TorextApp
from torext.utils import raise_exc_info
from torext.compat import httplib


def log_response(handler):
    """
    Acturally, logging response is not a server's responsibility,
    you should use http tools like Chrome Developer Tools to analyse the response.

    Although this function and its setting(LOG_RESPONSE) is not recommended to use,
    if you are laze as I was and working in development, nothing could stop you.
    """
    content_type = handler._headers.get('Content-Type', None)
    headers_str = handler._generate_headers()
    block = 'Response Infomations:\n' + headers_str.strip()

    if content_type and ('text' in content_type or 'json' in content_type):
        limit = 0
        if 'LOG_RESPONSE_LINE_LIMIT' in settings:
            limit = settings['LOG_RESPONSE_LINE_LIMIT']

        def cut(s):
            if limit and len(s) > limit:
                return [s[:limit]] + cut(s[limit:])
            else:
                return [s]

        body = ''.join(handler._write_buffer)
        lines = []
        for i in body.split('\n'):
            lines += ['| ' + j for j in cut(i)]
        block += '\nBody:\n' + '\n'.join(lines)
    app_log.info(block)


def log_request(handler):
    """
    Logging request is opposite to response, sometime its necessary,
    feel free to enable it.
    """
    block = 'Request Infomations:\n' + _format_headers_log(handler.request.headers)

    if handler.request.arguments:
        block += '+----Arguments----+\n'
        for k, v in handler.request.arguments.items():
            block += '| {0:<15} | {1:<15} \n'.format(repr(k), repr(v))

    app_log.info(block)


def _format_headers_log(headers):
    # length of '+-...-+' is 19
    block = '+-----Headers-----+\n'
    for k, v in headers.items():
        block += '| {0:<15} | {1:<15} \n'.format(k, v)
    return block


class BaseHandler(tornado.web.RequestHandler):
    """
    Request
        header:
        body:

    Response
        status code: 200(成功), 400(参数异常), 403(不成功), 404(web,未找到), 500(服务器异常)
        header:
        body:
    """
    EXCEPTION_HANDLERS = None

    PREPARES = []

    def _exception_default_handler(self, e):
        """This method is a copy of tornado.web.RequestHandler._handle_request_exception
        """
        if isinstance(e, HTTPError):
            if e.log_message:
                format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                app_log.warning(format, *args)
            if e.status_code not in httplib.responses:
                app_log.error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exc_info=sys.exc_info())
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info())
        else:
            app_log.error("Uncaught exception %s\n%r", self._request_summary(),
                          self.request, exc_info=True)
            self.send_error(500, exc_info=sys.exc_info())

    def _handle_request_exception(self, e):
        """This method handle HTTPError exceptions the same as how tornado does,
        leave other exceptions to be handled by user defined handler function
        maped in class attribute `EXCEPTION_HANDLERS`

        Common HTTP status codes:
            200 OK
            301 Moved Permanently
            302 Found
            400 Bad Request
            401 Unauthorized
            403 Forbidden
            404 Not Found
            405 Method Not Allowed
            500 Internal Server Error

        It is suggested only to use above HTTP status codes
        """
        handle_func = self._exception_default_handler
        if self.EXCEPTION_HANDLERS:
            for excs, func_name in self.EXCEPTION_HANDLERS.items():
                if isinstance(e, excs):
                    handle_func = getattr(self, func_name)
                    break

        handle_func(e)
        if not self._finished:
            self.finish()

    def head(self):
        """Make `curl -I` useable"""
        self.finish()

    @property
    def app(self):
        return TorextApp.current_app

    @property
    def db(self):
        """Rewrite this method to implement the default database connection object,
        eg. a sqlalchemy session

        Other names like ``mongodb``, ``redis``, ``memcache`` could also be used in this way.
        """
        raise NotImplementedError

    @property
    def json_decode(self):
        return self.app.json_decoder

    @property
    def json_encode(self):
        return self.app.json_encoder

    def flush(self, *args, **kwgs):
        """
        Before `RequestHandler.flush` was called, we got the final _write_buffer.

        This method will not be called in wsgi mode
        """
        if settings['LOG_RESPONSE'] and not self._status_code == 500:
            log_response(self)

        super(BaseHandler, self).flush(*args, **kwgs)

    def write_json(self, chunk, code=None, headers=None):
        """A convenient method that binds `chunk`, `code`, `headers` together

        chunk could be any type of (str, dict, list)
        """
        assert chunk is not None, 'None cound not be written in write_json'
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = self.json_encode(chunk)

        # convert chunk to utf8 before `RequestHandler.write()`
        # so that if any error occurs, we can catch and log it
        try:
            chunk = utf8(chunk)
        except Exception:
            app_log.error('chunk encoding error, repr: %s' % repr(chunk))
            raise_exc_info(sys.exc_info())

        self.write(chunk)

        if code:
            self.set_status(code)

        if headers:
            for k, v in headers.items():
                self.set_header(k, v)

    def write_file(self, file_path, mime_type=None):
        """Copy from tornado.web.StaticFileHandler
        """
        if not os.path.exists(file_path):
            raise HTTPError(404)
        if not os.path.isfile(file_path):
            raise HTTPError(403, "%s is not a file", file_path)

        stat_result = os.stat(file_path)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

        self.set_header("Last-Modified", modified)

        if not mime_type:
            mime_type, _encoding = mimetypes.guess_type(file_path)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                self.set_status(304)
                return

        with open(file_path, "rb") as file:
            data = file.read()
            hasher = hashlib.sha1()
            hasher.update(data)
            self.set_header("Etag", '"%s"' % hasher.hexdigest())
            self.write(data)

    def decode_signed_value(self, name, value, max_age_days=None):
        """Do what `RequestHandler.get_secure_cookie` does(when `value` is not None),
        but with a more friendly name

        What opposite to it is `RequestHandler.create_signed_value`
        """
        kwgs = {}
        if max_age_days is not None:
            kwgs['max_age_days'] = max_age_days
        return tornado.web.decode_signed_value(settings['COOKIE_SECRET'], name, value, **kwgs)

    def prepare(self):
        """Behaves like a middleware between raw request and handling process,

        If `PREPARES` is defined on handler class, which should be
        a list, for example, ['auth', 'context'], method whose name
        is constitute by prefix '_prepare_' and string in this list
        will be executed by sequence. In this example, those methods are
        `_prepare_auth` and `_prepare_context`
        """
        if settings['LOG_REQUEST']:
            log_request(self)

        for i in self.PREPARES:
            getattr(self, 'prepare_' + i)()
            if self._finished:
                return

    def render_string(self, template_name, **kwargs):
        """This method was rewritten to support multiple template engine
        (Determine by `TEMPLATE_ENGINE` setting, could be `tornado` and `jinja2`),
        it will only affect on template rendering process, ui modules feature,
        which is mostly exposed in `render` method, is kept to be used as normal.
        """
        if 'tornado' == settings['TEMPLATE_ENGINE']:
            return super(BaseHandler, self).render_string(template_name, **kwargs)
        elif 'jinja2' == settings['TEMPLATE_ENGINE']:
            return jinja2_render(template_name, **kwargs)
        else:
            raise errors.SettingsError(
                '%s is not a supported TEMPLATE_ENGINE, should be `tornado` or `jinja2`'
                % settings['TEMPLATE_ENGINE'])


class WSGIStreamHandler(BaseHandler):
    """
    http://flask.pocoo.org/snippets/116/
    http://www.html5rocks.com/en/tutorials/eventsource/basics/
    """
    def write_stream_queue(self, stream_queue):
        self._stream_queue = stream_queue

    def finish(self):
        """Finishes this response, ending the HTTP request."""
        if self._finished:
            raise RuntimeError("finish() called twice.  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")
        if not hasattr(self, '_stream_queue') or not self._stream_queue:
            raise RuntimeError("`_stream_queue` was not assigned, you should"
                               "call `write_stream_queue` to set.")

        # === Replace `if not self._headers_written` === #
        self.set_status(200)
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Access-Control-Allow-Origin", "*")
        # ============================================== #

        self.request.connection.set_close_callback(None)

        # === Add before self.flush === #
        # Reset buffer
        self._write_buffer = []
        self._headers_written = False
        # ============================= #

        self.flush(include_footers=True)

        # === Add after self.flush === #
        self._write_buffer = self._stream_queue
        self.request.connection._write_buffer = self._stream_queue
        # ============================ #

        self.request.finish()
        self._log()
        self._finished = True
        self.on_finish()
        # Break up a reference cycle between this handler and the
        # _ui_module closures to allow for faster GC on CPython.
        self.ui = None


_jinja2_env = None


def jinja2_render(template_name, **kwargs):
    env = get_jinja2_env()
    template = env.get_template(template_name)
    return template.render(**kwargs)


def get_jinja2_env():
    from jinja2 import Environment, PackageLoader

    global _jinja2_env
    if not _jinja2_env:
        _jinja2_env = Environment(loader=PackageLoader(settings['PROJECT'], settings['TEMPLATE_PATH']))
    return _jinja2_env
