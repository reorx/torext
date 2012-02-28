#!/usr/bin/python
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
import traceback

import tornado.web
import tornado.locale

from tornado.web import HTTPError
from tornado import escape

from torext import settings
from torext.utils.format import _json, _dict


def block_response_text(text, width=80, limit=800):
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
    return block


class _BaseHandler(tornado.web.RequestHandler):
    __prepares__ = []
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

    @property
    def mysql(self):
        """Return the default master MySQL session"""
        raise NotImplementedError
        #return self.application.connections.get('mysql', 'master')

    @property
    def mongodb(self):
        """Return the default MongoDB databse"""
        raise NotImplementedError
        #return self.application.connections.get('mongodb', 'master')

    @property
    def mq(self):
        raise NotImplementedError

    @property
    def dump_dict(self):
        return _json

    @property
    def parse_json(self):
        return _dict

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

        if settings.debug:
            logging.debug(block_response_text(chunk))

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
            msg['error'] = error.__str__()
            if settings.debug:
                msg['traceback'] = '\n' + traceback.format_exc()
        elif isinstance(error, str):
            msg['error'] = error
        else:
            raise ValueError('error object should be either Exception or str')

        self.write(msg)
        if not self._finished:
            self.finish()

        if settings.debug:
            logging.error(msg['error'] + '\n' + msg['traceback'])

    def file_write(self, byteStream, mime='text/plain'):
        self.set_header("Content-Type", mime)
        self.write(byteStream)
        if not self._finished:
            self.finish()

    # TODO get_user_locale

    def get_auth_value(self, name, value, max_age_days=7):
        """Changed. user new function: tornado.web.RequestHandler.create_signed_value
        """
        return tornado.web.decode_signed_value(self.application.settings['auth_secret'],
                                               name, value, max_age_days=max_age_days)

    def set_auth_value(self, name, value):
        """Written as set_secure_cookie works
        """
        return tornado.web.create_signed_value(self.application.settings['auth_secret'],
                                               name, value)

    def prepare(self):
        """
        like a middleware between raw request and handling process,
        """
        if settings.debug:
            self._prepare_debug()
            if self._finished:
                return
        for i in self.__prepares__:
            logging.debug('prepare:: %s' % i)
            getattr(self, '_prepare_' + i)()
            if self._finished:
                return

    def _prepare_debug(self, with_value=True):
        """
        """
        block = '-> Request\n'
        block += '-----Headers-----\n'
        for k, v in self.request.headers.iteritems():
            tmpl = '| {0:<15} | {1:<15} \n'
            block += tmpl.format(k, v)
        if self.request.arguments:
            block += '-----Arguments-----\n'
            for k, v in self.request.arguments.iteritems():
                tmpl = '| {0:<15} | {1:<15} \n'
                req_body = tmpl.format(repr(k), repr(v))
                if not settings.debug_full_request:
                    if req_body[1000:]:
                        req_body = req_body[:1000] + '... ...'
                    else:
                        req_body = req_body[:1000]
                block += req_body

        logging.info(block)

    def render(self, template_name, context={}):
        """for web using"""
        return super(_BaseHandler, self).render(template_name, **context)


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


def api_define(method):
    pass
