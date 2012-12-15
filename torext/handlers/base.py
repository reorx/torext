#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import httplib
import functools
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
from tornado import escape
from tornado.util import raise_exc_info

from torext import settings, errors
from torext.utils import ObjectDict, _json, _dict
from torext.app import TorextApp


def _format_headers_log(headers):
    # length of '+-...-+' is 19
    block = '+-----Headers-----+\n'
    for k, v in headers.iteritems():
        block += '| {0:<15} | {1:<15} \n'.format(k, v)
    return block


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
    logging.info(block)


def log_request(handler):
    """
    Logging request is opposite to response, sometime its necessary,
    feel free to enable it.
    """
    block = 'Request Infomations:\n' + _format_headers_log(handler.request.headers)

    if handler.request.arguments:
        block += '+----Arguments----+\n'
        for k, v in handler.request.arguments.iteritems():
            block += '| {0:<15} | {1:<15} \n'.format(repr(k), repr(v))

    logging.info(block)


class _BaseHandler(tornado.web.RequestHandler):
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

    def initialize(self):
        logging.debug('%s initializing' % self.__class__.__name__)

    def _exception_default_handler(self, e):
        """This method is a copy of tornado.web.RequestHandler._handle_request_exception
        """
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
            logging.error("Uncaught exception %s\n%r", self._request_summary(),
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
            for excs, func_name in self.EXCEPTION_HANDLERS.iteritems():
                if isinstance(e, excs):
                    handle_func = getattr(self, func_name)
                    break

        handle_func(e)
        if not self._finished:
            self.finish()

    @property
    def app(self):
        return TorextApp.current_app

    @property
    def db(self):
        """Return the default sqlalchemy session"""
        raise NotImplementedError

    @property
    def mongodb(self):
        """Return the default MongoDB databse"""
        raise NotImplementedError

    @property
    def dump_dict(self):
        return _json

    @property
    def parse_json(self):
        return _dict

    def flush(self, *args, **kwgs):
        """
        Before `RequestHandler.flush` was called, we got the final _write_buffer.

        This method will not be called in wsgi mode
        """
        if settings['LOG_RESPONSE'] and not self._status_code == 500:
            log_response(self)

        super(_BaseHandler, self).flush(*args, **kwgs)

    def json_write(self, chunk, code=None, headers=None):
        """A convenient method to bind `chunk`, `code`, `headers` together

        chunk could be any type of (str, dict, list)
        """
        assert chunk is not None, 'None cound not be written in json_write'
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = self.dump_dict(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")

        # convert chunk to utf8 before `RequestHandler.write()`
        # so that if any error occurs, we can catch and log it
        try:
            chunk = escape.utf8(chunk)
        except Exception:
            logging.error('chunk encoding error, repr: %s' % repr(chunk))
            raise_exc_info(sys.exc_info())

        self.write(chunk)

        if code:
            self.set_status(code)

        if headers:
            for k, v in headers.iteritems():
                self.set_header(k, v)

    def file_write(self, file_path, mime_type=None):
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
            getattr(self, '_prepare_' + i)()
            if self._finished:
                return


class define_api(object):
    """Decorator for validating request arguments and raising relevant exception

    Example:
    >>> _user_data_api = define_api(
            [
                ('username', True,
                    WordsValidator(4, 16, 'must be words in 4~16 range')),
                ('password', True,
                    RegexValidator(6, 32, 'must be words&symbols in 6~32 range',
                                    regex=re.compile(r'^[A-Za-z0-9@#$%^&+=]+$'))),
            ]
        )
    >>> class UserHandler(BaseHandler):
            @ _user_data_api
            def get(self):
                ...

    NOTE. This class is deprecated since `torext.validators.Params` can replace it and do better,
    """
    def __init__(self, rules, extra_validator=None):
        """
        rules:
            [
                ('arg_name0', ),
                ('arg_name1', True, WordsValidator())
                ('arg_name2', False, IntstringValidator())
            ]
        """
        self.rules = rules
        self.extra_validator = extra_validator

    def __call__(self, method):
        @functools.wraps(method)
        def wrapper(hdr, *args, **kwgs):

            params = ObjectDict()
            extra_validator = self.extra_validator
            error_list = []

            for rule in self.rules:
                if isinstance(rule, str):
                    rule = (rule, False)
                assert len(rule) > 1 and len(rule) < 4

                key = rule[0]
                is_required = rule[1]

                value = hdr.get_argument(key, None)

                # judge existence
                if not value:
                    if is_required:
                        error_list.append('missing param: %s' % key)
                    continue

                # judge validator
                if len(rule) == 3:
                    validator = rule[2]
                    try:
                        value = validator(value)
                    except errors.ValidationError, e:
                        error_list.append(u'param %s, %s' % (key, e))

                # if len(rule) == 3:
                #     typ = rule[2]
                #     try:
                #         value = typ(value)
                #     except ValueError:
                #         error_list.append('error type of param %s, should be %s' % (key, typ))

                params[key] = value

            if error_list:
                raise errors.ParametersInvalid(
                    '; '.join(['%s.%s' % (i + 1, v) for i, v in enumerate(error_list)]))

            logging.debug('params: %s' % params)

            if extra_validator:
                try:
                    extra_validator(params)
                except errors.ValidationError, e:
                    raise errors.ParametersInvalid(e)
                # message = 'failed in extra validator checking'

            hdr.params = params

            return method(hdr, *args, **kwgs)

        return wrapper
