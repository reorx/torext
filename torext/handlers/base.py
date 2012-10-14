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

import logging
import urllib
import urlparse
import functools
# import traceback

import tornado.web
import tornado.locale

from tornado.web import HTTPError
from tornado import escape

from torext import settings, errors
from torext.utils import ObjectDict, _json, _dict


def log_response(text, width=80, limit=800):
    if isinstance(text, str):
        text = text.decode('utf-8')

    if len(text) > limit:
        text = text[:limit - 1]
        end = ' ...'
    else:
        end = ''

    block = '-> Response\n'
    while text:
        block += '| ' + text[:width] + '\n'
        text = text[width:]
    block += end

    logging.info(block)


def log_request(handler, with_value=True):
    """
    """
    block = 'Request Infomations ->\n-----Headers-----\n'

    for k, v in handler.request.headers.iteritems():
        block += '| {0:<15} | {1:<15} \n'.format(k, v)

    if handler.request.arguments:
        block += '-----Arguments-----\n'
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
        logging.error("Uncaught exception %s\n%r", self._request_summary(),
                      self.request, exc_info=True)
        if 'BUG_REPORTER' in settings:
            # TODO
            # bug_report.delay(self.get_current_timestamp(), e, traceback.format_exc(),
            #     settings.bug_reporter)
            pass

        return self.json_error(500, e)

    def _handle_request_exception(self, e):

        ## Original handling, from tornado.web
        if isinstance(e, errors.HTTPError):
            if e.log_message:
                format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                logging.warning(format, *args)

            # Redefined HTTPError handling
            self.json_error(e.status_code, e)
        ## End original handling

        else:
            handle_func = self._default_handle_exception
            if hasattr(self, 'HTTP_STATUS_EXCEPTIONS'):
                for excs, func_name in self.HTTP_STATUS_EXCEPTIONS.iteritems():
                    if isinstance(e, excs):
                        handle_func = getattr(self, func_name)

            handle_func(e)

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

    def write(self, chunk, *args, **kwgs):
        super(_BaseHandler, self).write(chunk, *args, **kwgs)

        if settings['LOG_RESPONSE']:
            log_response(chunk)

    def json_write(self, chunk, json=False, headers={}):
        """
        Used globally, not special in ApiHandler
        chunk could be any type of str, dict, list
        """
        if json:
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        if headers:
            for k, v in headers.iteritems():
                self.set_header(k, str(v))
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = self.dump_dict(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = escape.utf8(chunk)

        self.write(chunk)
        if not self._finished:
            self.finish()

    def json_error(self, code, error=None):
        """Used globally, not special in ApiHandler
        """
        # TODO show message on logging
        self.set_status(code)

        msg = {
            'code': code,
            'error': '',
        }
        if isinstance(error, Exception):
            # NOTE if use __str__() it will cause UnicodeEncodeError when error contains Chinese unicode
            msg['error'] = error.__unicode__()

            # not using this currently
            # if settings['DEBUG'] and not isinstance(error, HTTPError):
            #     msg['traceback'] = '\n' + traceback.format_exc()
            #     logging.error(msg['error'] + '\n' + msg['traceback'])
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.write(msg)
        if not self._finished:
            self.finish()

    def file_write(self, byteStream, mime='text/plain'):
        self.set_header("Content-Type", mime)
        self.write(byteStream)
        if not self._finished:
            self.finish()

    # TODO get_user_locale

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
