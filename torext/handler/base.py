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

import tornado.web
import tornado.locale

from tornado.web import HTTPError
from tornado import escape
from tornado.options import options

from ..utils.format import _json, _dict


class _BaseHandler(tornado.web.RequestHandler):
    __prepares__ = ['debug']
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
            logging.info('%s initializing' % self.__class__.__name__)

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
    def dump_json(self):
        return _json

    @property
    def parse_json(self):
        return _dict

    def json_write(self, chunk, json=False):
        """Used globally, not special in ApiHandler
        chunk could be any type of str, dict, list
        """
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = self.dump_json(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = escape.utf8(chunk)
        if options.application['debug']:
            import copy
            text = copy.copy(chunk)
            op = ''
            ed = None
            width = 80
            limit = 800
            l = len(text)
            if l > limit:
                text = text[:limit-1]
                l = limit
                ed = ' ...'
            height = l/width
            if l - (l/width)*width > 0:
                height += 1
            for i in range(height):
                op += ' | ' + text[i*width:(i+1)*width-1]
                if i == height-1 and ed is not None:
                    op += ed
                op += '\n'
            print ' [ Response'
            print op
        if json:
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(chunk)

    def json_error(self, code, text=None):
        """Used globally, not special in ApiHandler
        """
        # TODO show message on logging
        self.set_status(code)
        msg = {'code': code, 'error': text}
        print 'API ERROR: ', msg
        self.write(msg)
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
        for i in self.__prepares__:
            logging.info('prepare:: %s' % i)
            getattr(self, '_prepare_'+i)()
            if self._finished: return

    def _prepare_debug(self, with_value=True):
        """
        """
        def print_dict_keys(d):
            fmt = ' | {0:<15}'
            d_keys = d.keys()
            d_keys.sort()
            d_op = ''
            for loop, i in enumerate(d_keys):
                d_op += fmt.format(i)
                if loop == len(d_keys)-1:
                    d_op += ' ]'
                elif (loop+1)%4 == 0:
                    d_op += ' |\n'
                else:
                    pass
            print d_op

        def print_dict(d):
            fmt = ' | {0:<15}: {1:<15}'
            d_keys = d.keys()
            d_keys.sort()
            d_op = ''
            for loop, i in enumerate(d_keys):
                v = d[i]
                if isinstance(v, list) or isinstance(v, tuple):
                    v = v[0]
                d_op += fmt.format(i, v)
                if loop == len(d_keys)-1:
                    d_op += ' ]'
                else:
                    d_op += '\n'
            print d_op

        if not with_value:
            print ' [ {0:<15} |'.format('Request Headers')
            print_dict_keys(self.request.headers)
            print ' [ {0:<15} |'.format('Request Params')
            print_dict_keys(self.request.arguments)
        else:
            print ' [ {0:<15}'.format('Request Headers')
            print_dict(self.request.headers)
            print ' [ {0:<15}'.format('Request Params')
            print_dict(self.request.arguments)
        print ''


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
