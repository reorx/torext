#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.handlers.oauth import TwitterOAuthMixin
from torext.app import TorextApp
from torext.handlers import _BaseHandler
from tornado.web import asynchronous


app = TorextApp()
app.settings['TWITTER'] = {
    'consumer_key': 'UykIAIg0r0tfkXiSfrzhg',
    'consumer_secret': 'IeRH6aB708tOdXh6ntRh0pWn43WPSEamzzAp7eww'
}


_url_prefix = 'http://127.0.0.1:8000'


@app.route('/tw')
class TestTwitter(_BaseHandler, TwitterOAuthMixin):
    @asynchronous
    def get(self):
        if self.get_argument('oauth_token', None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
        self.authorize_redirect(callback_uri=_url_prefix + '/tw')

    def _on_auth(self, user):
        print user


if __name__ == '__main__':
    app.run()
