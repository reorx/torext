#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.handlers import oauth
from torext.app import TorextApp
from torext.handlers import _BaseHandler
from tornado.web import asynchronous

import settings

app = TorextApp(settings)

_url_prefix = 'http://127.0.0.1:8000'


class BaseHandler(_BaseHandler):
    def _on_auth(self, user):
        print 'user', user
        if not user:
            self.write('failed, retry')
            return self.finish()
        self.json_write(user)
        self.finish()


@app.route('/')
class HomeHandler(BaseHandler):
    def get(self):
        self.json_write(app.settings)


@app.route('/tw')
class TwitterHandler(BaseHandler, oauth.TwitterOAuthMixin):
    @asynchronous
    def get(self):
        if self.get_argument('oauth_token', None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
        else:
            self.authorize_redirect(callback_uri=_url_prefix + '/tw')


@app.route('/fb')
class FacebookHandler(BaseHandler, oauth.FacebookOAuth2Mixin):
    @asynchronous
    def get(self):
        if self.get_argument("code", False):
            self.get_authenticated_user(
                code=self.get_argument("code"),
                callback=self.async_callback(self._on_auth))
            return
        self.authorize_redirect()


@app.route('/douban')
class DoubanHandler(BaseHandler, oauth.DoubanOAuthMixin):
    @asynchronous
    def get(self):
        if self.get_argument('oauth_token', None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
        else:
            self.authorize_redirect(callback_uri=_url_prefix + '/tw')


if __name__ == '__main__':
    app.run()
