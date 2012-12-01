#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
core concepts:
    * client
        name collection, could be mobile or browser

    * browser
        one in client

    * mobile
        one in client

    * web
        request send by a browser called web request

    * api
        request send by a mobile called api request
"""

import sys
import logging
import urllib
import urlparse
import functools
import traceback

import tornado.web
import tornado.locale

from tornado.web import HTTPError
from tornado import escape

from torext import settings, errors
from torext.utils import ObjectDict, _json, _dict


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
    PREPARES = []
    """
    Request
        header:
        body:

    Response
        status code: 200(成功), 400(参数异常), 403(不成功), 404(web,未找到), 500(服务器异常)
        header:
        body:
    """
    _first_running = True

    def initialize(self):
        if self.__class__._first_running:
            self.__class__._first_running = False
            logging.debug('%s initializing' % self.__class__.__name__)

    def _default_handle_exception(self, e):
        ## Actually the first part of Request._handle_request_exception
        logging.error("Uncaught exception %s\n%r", self._request_summary(),
                      self.request, exc_info=True)
        self.send_error(500, exc_info=sys.exc_info())

    def _handle_request_exception(self, e):
        import sys
        import httplib

        ## Original handling, from tornado.web
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
        ## End original handling

        else:
            handle_func = self._default_handle_exception
            if hasattr(self, 'HTTP_STATUS_EXCEPTIONS'):
                for excs, func_name in self.HTTP_STATUS_EXCEPTIONS.iteritems():
                    if isinstance(e, excs):
                        handle_func = getattr(self, func_name)
                        break

            handle_func(e)
            if not self._finished:
                self.finish()

    @property
    def mysql(self):
        """Return the default master MySQL session"""
        raise NotImplementedError

    @property
    def mongodb(self):
        """Return the default MongoDB databse"""
        raise NotImplementedError

    @property
    def mq(self):
        """Return the default Message Queue connection"""
        raise NotImplementedError

    @property
    def dump_dict(self):
        return _json

    @property
    def parse_json(self):
        return _dict

    def flush(self, *args, **kwgs):
        # Before RequestHandler.flush was called, we got the
        # final _write_buffer.
        if settings['LOG_RESPONSE'] and not self._status_code == 500:
            log_response(self)

        super(_BaseHandler, self).flush(*args, **kwgs)

    def json_write(self, chunk, headers={}):
        """
        chunk could be any type of str, dict, list
        """
        if headers:
            for k, v in headers.iteritems():
                self.set_header(k, str(v))
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = self.dump_dict(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")

        # pre-doing utf8 convert before RequestHandler.write()
        # so that if any error occurs, we can find it
        try:
            chunk = escape.utf8(chunk)
        except Exception, e:
            logging.error('chunk encoding error in _BaseHandler.json_write, raise')
            raise e

        self.write(chunk)

    def json_error(self, code, error=None):
        msg = {'code': code}
        if isinstance(error, Exception):
            # NOTE(maybe) if use __str__() it will cause UnicodeEncodeError when error contains Chinese unicode
            # msg['error'] = error.__unicode__()
            msg['error'] = str(error)
            logging.warning('Get exception in json_error: %s - %s' %
                            (error.__class__.__name__, error))
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.set_status(code)
        self.json_write(msg)

    def file_write(self, byteStream, mime='text/plain'):
        self.set_header("Content-Type", mime)
        self.write(byteStream)
        if not self._finished:
            self.finish()

    def decode_auth_token(self, name, token, max_age_days=None):
        """Changed. user new function: tornado.web.RequestHandler.create_signed_value
        """
        if max_age_days is None:
            max_age_days = settings['COOKIE_EXPIRE_DAY']
        return tornado.web.decode_signed_value(settings['COOKIE_SECRET'],
                                               name, token, max_age_days=max_age_days)

    def encode_auth_value(self, name, value):
        """Written as set_secure_cookie works
        """
        return tornado.web.create_signed_value(settings['COOKIE_SECRET'],
                                               name, value)

    def prepare(self):
        """
        like a middleware between raw request and handling process,
        """
        if settings['LOG_REQUEST']:
            log_request(self)
        if False:
            print 'shit'

        for i in self.PREPARES:
            getattr(self, '_prepare_' + i)()
            if self._finished:
                return


def api_authenticated(method):
    """Copy from tornado.web.authenticated.

    no need to use in ApiAuthedHandler
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


class define_api(object):
    def __init__(self, rules, extra_validator=None):
        """
        :defs::
        [
            ('arg_name0', ),
            ('arg_name1', True, WordsValidator())
            ('arg_name2', False, IntstringValidator())
        ], Validator()
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
