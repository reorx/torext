#!/usr/bin/env python
# -*- coding: utf-8 -*-


# from shiao's tornado.third.renren
# sina weibo
# oauth2 mixin classes

import logging
import urllib
import urlparse
import hashlib
import requests
import time
from tornado import escape
from tornado import httpclient
from tornado import gen
from tornado.escape import json_decode
from tornado.httputil import url_concat
from tornado.auth import OAuthMixin, OAuth2Mixin
from tornado.util import bytes_type

from torext import settings

#
# TODO move the consumer_* arguments out of classes
#

####################
# oauth 1.0 & 1.0a #
####################


class TwitterOAuthMixin(OAuthMixin):
    # copy from tornado.auth
    _OAUTH_REQUEST_TOKEN_URL = "http://api.twitter.com/oauth/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "http://api.twitter.com/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "http://api.twitter.com/oauth/authorize"
    _OAUTH_AUTHENTICATE_URL = "http://api.twitter.com/oauth/authenticate"

    def authenticate_redirect(self):
        http = httpclient.AsyncHTTPClient()
        http.fetch(self._oauth_request_token_url(), self.async_callback(
            self._on_request_token, self._OAUTH_AUTHENTICATE_URL, None))

    def twitter_request(self, path, callback, access_token=None,
                        post_args=None, **args):
        # Add the OAuth resource request signature if we have credentials
        # NOTE varibles::
        # :url        used to send request, and bear encoded `args`.
        # :args       keyword-arguments that additionaly added to oauth parameters,
        #             lay on `url`.
        # :post_args  use to judge request method, must be passed as post-data
        # :all_args   as every argument in request take activity
        #             when oauth-parameters is generated, `all_args` contain `args` and `post_args`
        url = "http://api.twitter.com/1" + path + ".json"
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        if args:
            url += "?" + urllib.urlencode(args)
        callback = self.async_callback(self._on_twitter_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_twitter_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        return dict(
            key=settings['TWITTER']['consumer_key'],
            secret=settings['TWITTER']['consumer_secret'])

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.twitter_request(
            "/users/show/" + access_token["screen_name"],
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        if user:
            user["username"] = user["screen_name"]
        callback(user)


class WeiboOAuthMixin(OAuthMixin):
    _OAUTH_REQUEST_TOKEN_URL = "http://api.t.sina.com.cn/oauth/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "http://api.t.sina.com.cn/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "http://api.t.sina.com.cn/oauth/authorize"
    _OAUTH_API_DOMAIN = "api.t.sina.com.cn"

    def weibo_request(self, path, callback, access_token=None,
                      post_args=None, **args):
        url = "http://" + self._OAUTH_API_DOMAIN + path + ".json"
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        if args:
            url += "?" + urllib.urlencode(args)
        callback = self.async_callback(self._on_weibo_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_weibo_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        return dict(key=settings.networks['weibo']['consumer_key'],
                    secret=settings.networks['weibo']['consumer_secret'])

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.weibo_request(
            "/users/show",
            access_token=access_token, callback=callback,
            user_id=access_token["user_id"])

    def _parse_user_response(self, callback, user):
        if user:
            user["username"] = user["screen_name"]
        callback(user)


class DoubanOAuthMixin(OAuthMixin):
    _OAUTH_REQUEST_TOKEN_URL = "http://www.douban.com/service/auth/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "http://www.douban.com/service/auth/access_token"
    _OAUTH_AUTHORIZE_URL = "http://www.douban.com/service/auth/authorize"
    _OAUTH_API_DOMAIN = "api.douban.com"
    _OAUTH_VERSION = "1.0"

    def douban_request(self, path, callback, access_token=None,
                       post_args=None, **args):
        # due to some special string like ``@`` may appear in url,
        # and they are required to be quoted before generated to be oauth parameters,
        # (unfortunately tornado don't voluntarily do that)
        # we forwardly quote the url before it is handled.
        url = urllib.quote("http://" + self._OAUTH_API_DOMAIN + path, ':/')

        # reset `format` value in args
        args['alt'] = 'json'

        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        http = httpclient.AsyncHTTPClient()
        callback = self.async_callback(self._on_douban_request, callback)

        if post_args is not None:
            # douban says that they can't deal request properly
            # when oauth parameters passing in post data,
            # instead, passing it in HTTP Headers
            # NOTE that `url` here is different from `url` in below fetch function:
            # it is plain, doesn't contain encoded args.
            http.fetch(url, method="POST",
                       headers=args,
                       body=post_args,
                       callback=callback)
        else:
            if args:
                url += "?" + urllib.urlencode(args)
            http.fetch(url, callback=callback)

    def _on_douban_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        return dict(key=settings.networks['douban']['consumer_key'],
                    secret=settings.networks['douban']['consumer_secret'])

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.douban_request(
            "/people/@me",
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        if user:
            user["uid"] = user["db:uid"]["$t"]
        callback(user)


class TencentOAuthMixin(OAuthMixin):
    _OAUTH_REQUEST_TOKEN_URL = "http://open.t.qq.com/cgi-bin/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "http://open.t.qq.com/cgi-bin/access_token"
    _OAUTH_AUTHORIZE_URL = "http://open.t.qq.com/cgi-bin/authorize"
    _OAUTH_API_DOMAIN = "open.t.qq.com/api"
    #_OAUTH_VERSION = "1.0"

    def tencent_request(self, path, callback, access_token=None,
                        post_args=None, **args):
        # as Tencent is so fucking shit
        # that it use OAuth1.0a but only let the parameter
        # ``oauth_version`` pass value of 1.0,
        # there will be very fucking weird problem occurs
        # if we don't manually change the _OAUTH_VERSION to be 1.0
        # before oauth parameters are generated
        self._OAUTH_VERSION = '1.0'

        url = urllib.quote("http://" + self._OAUTH_API_DOMAIN + path, ':/')

        # reset `format` value in args
        args['format'] = 'json'

        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        if args:
            url += "?" + urllib.urlencode(args)
        http = httpclient.AsyncHTTPClient()
        callback = self.async_callback(self._on_tencent_request, callback)

        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_tencent_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        return dict(key=settings.networks['tencent']['consumer_key'],
                    secret=settings.networks['tencent']['consumer_secret'])

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.tencent_request(
            "/user/info",
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        print 'user', user
        if user:
            user["username"] = user["data"]["name"]
        callback(user)


#############
# oauth 2.0 #
#############


class FacebookOAuth2Mixin(OAuth2Mixin):
    # copy from tornado.auth
    """Facebook authentication using the new Graph API and OAuth2."""
    _OAUTH_ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token?"
    _OAUTH_AUTHORIZE_URL = "https://graph.facebook.com/oauth/authorize?"

    def authorize_redirect(self):
        options = settings['FACEBOOK']
        extra_params = None
        if options.get('scope', None):
            extra_params = {'scope': options['scope']}
        super(FacebookOAuth2Mixin, self).authorize_redirect(
            redirect_uri=options['redirect_uri'],
            client_id=options['consumer_key'],
            extra_params=extra_params)

    def get_authenticated_user(self, code, callback, extra_fields=None):
        http = httpclient.AsyncHTTPClient()
        options = settings['FACEBOOK']
        args = {
            "code": code,
            "client_id": options['consumer_key'],
            "client_secret": options['consumer_secret'],
            "redirect_uri": options['redirect_uri'],
        }

        fields = set(['id', 'name', 'first_name', 'last_name',
                      'locale', 'picture', 'link'])
        if extra_fields:
            fields.update(extra_fields)

        http.fetch(self._oauth_request_token_url(**args),
                   self.async_callback(self._on_access_token, callback, fields))

    def _on_access_token(self, callback, fields, response):
        if response.error:
            logging.warning('Facebook auth error: %s' % response)
            callback(None)
            return

        args = escape.parse_qs_bytes(escape.native_str(response.body))
        session = {
            "access_token": args["access_token"][-1],
            "expires": args.get("expires")
        }

        self.facebook_request(
            path="/me",
            callback=self.async_callback(
                self._on_get_user_info, callback, session, fields),
            access_token=session["access_token"],
            fields=",".join(fields)
        )

    def _on_get_user_info(self, callback, session, fields, user):
        if user is None:
            callback(None)
            return

        fieldmap = {}
        for field in fields:
            fieldmap[field] = user.get(field)

        fieldmap.update({"access_token": session["access_token"], "session_expires": session.get("expires")})
        callback(fieldmap)

    def facebook_request(self, path, callback, access_token=None,
                         post_args=None, **args):
        url = "https://graph.facebook.com" + path
        all_args = {}
        if access_token:
            all_args["access_token"] = access_token
            all_args.update(args)
            all_args.update(post_args or {})
        if all_args:
            url += "?" + urllib.urlencode(all_args)
        callback = self.async_callback(self._on_facebook_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_facebook_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))


class WeiboOAuth2Mixin(object):
    _OAUTH_AUTHORIZE_URL = "https://api.weibo.com/oauth2/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://api.weibo.com/oauth2/access_token"

    _OAUTH_URL = "https://api.weibo.com/2/"

    @gen.engine
    def weibo_request(self, path, access_token, callback, data=None, **args):
        url = self._OAUTH_URL + path
        if data is not None:
            requests.post(url, data=data)
        else:
            pass
        return

    @gen.engine
    def get_authenticated_user(self, code, callback):
        self.get_access_token(
            code, callback=(yield gen.Callback('WeiboGraphMixin.get_authenticated_user')))

        token_dict = yield gen.Wait('WeiboGraphMixin.get_authenticated_user')
        if not token_dict:
            callback(None)
            return

        callback('success')

    def authorize_redirect(self,
                           response_type='code',
                           extra_display=None,
                           state=None,
                           **kwgs):
        consumer_token = self._oauth_consumer_token()
        assert (response_type in ('code', 'token')), 'argument:response_type incorrect'
        display_list = ['default', ]
        if extra_display is not None:
            display_list.extend(extra_display)
        display = ','.join(display_list)
        all_args = {
            'client_id': consumer_token['client_id'],
            'redirect_uri': settings.networks['weibo']['redirect_uri'],
            'response_type': response_type,
            'display': display,
        }
        all_args.update(kwgs)
        self.redirect(url_concat(self._OAUTH_AUTHORIZE_URL, all_args))

    @gen.engine
    def get_access_token(self, code, callback,
                         grant_type='authorization_code',
                         **kwgs):
        consumer_token = self._oauth_consumer_token()
        assert (grant_type in ('authorization_code', 'password', 'refresh_token')), 'argument:response_type incorrect'
        all_args = {
            'client_id': consumer_token['client_id'],
            'client_secret': consumer_token['client_secret'],
            'grant_type': grant_type,
        }
        if 'authorization_code' == grant_type:
            all_args['code'] = code
            all_args['redirect_uri'] = settings.networks['weibo']['redirect_uri']
        elif 'password' == grant_type:
            for k in ('username', 'password'):
                assert k in kwgs, 'argument:%s is required' % k
                all_args[k] = kwgs[k]
        else:  # 'refresh_token' == grant_type
            for k in ('refresh_token', ):
                assert k in kwgs, 'argument:%s is required' % k
                all_args[k] = kwgs[k]

        # NOTE will cause this error:
        # SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed
        #
        #http = httpclient.AsyncHTTPClient()
        #req = httpclient.HTTPRequest(self._OAUTH_ACCESS_TOKEN_URL,
                #body=urllib.urlencode(all_args))
        #http.fetch(req,
                   #callback=(yield gen.Callback('WeiboGraphMixin.get_access_token')))
        #response = yield gen.Wait('WeiboGraphMixin.get_access_token')
        response = requests.post(self._OAUTH_ACCESS_TOKEN_URL, all_args)

        if response.error:
            logging.warning("Error response %s fetching %s",
                            response.error, response.url)
            callback(None)
            return

        token_dict = json_decode(response.read())
        callback(token_dict)

    def _oauth_consumer_token(self):
        token = dict(client_id=settings.networks['weibo']['consumer_key'],
                     client_secret=settings.networks['weibo']['consumer_secret'],)
        return token


class RenrenOAuth2Mixin(object):
    _OAUTH_AUTHORIZE_URL = "https://graph.renren.com/oauth/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://graph.renren.com/oauth/token"

    _OAUTH_URL = "https://graph.renren.com/"

    @gen.engine
    def renren_request(self, path, access_token, callback,
                       post_args=None, **args):
        http = httpclient.AsyncHTTPClient()
        url = self._OAUTH_URL + path
        if post_args is not None:
            #TODO as renren has not release graph resource support
            # method POST
            pass
        else:
            args['oauth_token'] = access_token
            http.fetch(
                url_concat(url, args),
                callback=(yield gen.Callback('_RenrenGraphMixin.renren_request'))
            )
        response = yield gen.Wait('_RenrenGraphMixin.renren_request')
        if response.error and not response.body:
            logging.warning("Error response %s fetching %s",
                            response.error, response.request.url)
            callback(None)
            return
        callback(response)
        return

    @gen.engine
    def get_authenticated_user(self, redirect_uri, callback, scope=None, **args):
        """
        class RenrenHandler(tornado.web.RequestHandler, RenrenGraphMixin):
            @tornado.web.asynchronous
            @gen.engine
            def get(self):
                self.get_authenticated_user(
                    callback=(yield gen.Callback('key')),
                    redirect_uri=url)
                user = yield gen.Wait('key')
                if not user:
                    raise web.HTTPError(500, "Renren auth failed")
                # do something else
                self.finish()
        """

        code = self.get_argument('code', None)
        if not code:
            self.authorize_redirect(redirect_uri, scope=scope, **args)
            return
        self.get_access_token(
            code, callback=(yield gen.Callback('_RenrenGraphMixin.get_authenticated_user')),
            redirect_uri=redirect_uri)

        response = yield gen.Wait('_RenrenGraphMixin.get_authenticated_user')
        if not response:
            callback(None)
            return
        try:
            user = json_decode(response.body)
        except:
            logging.warning("Error response %s fetching %s",
                            response.body, response.request.url)
            callback(None)
            return
        if 'error' in user:
            logging.warning("Error response %s fetching %s",
                            user['error_description'], response.request.url)
            callback(None)
            return

        #{{{ get session key
        self.renren_request('renren_api/session_key', user['access_token'],
                            callback=(yield gen.Callback('_RenrenGraphMixin._session_key')))
        response = yield gen.Wait('_RenrenGraphMixin._session_key')
        if response.error and not response.body:
            logging.warning("Error response %s fetching %s",
                            response.error, response.request.url)
        elif response.error:
            logging.warning("Error response %s fetching %s: %s",
                            response.error, response.request.url, response.body)
        else:
            try:
                user['session'] = json_decode(response.body)
            except:
                pass
        #}}} #TODO delete when renren graph api released
        callback(user)
        return

    def authorize_redirect(self, redirect_uri, response_type='code', scope=None, **args):
        consumer_token = self._oauth_consumer_token()
        all_args = {
            'client_id': consumer_token['key'],
            'redirect_uri': redirect_uri,
            'response_type': response_type,
        }
        if scope:
            all_args.update({'scope': scope})
        args.update(all_args)
        self.redirect(url_concat(self._OAUTH_AUTHORIZE_URL, args))

    @gen.engine
    def get_access_token(self, code, callback, grant_type='code', redirect_uri=None):
        consumer_token = self._oauth_consumer_token()
        args = {
            'client_id': consumer_token['key'],
            'client_secret': consumer_token['secret'],
        }
        if grant_type == 'refresh_token':
            args.update(
                grant_type='refresh_token',
                refresh_token=code,
            )
        elif redirect_uri:
            args.update(
                grant_type='authorization_code',
                code=code,
                redirect_uri=redirect_uri,
            )
        else:
            logging.error('Renren Get Access Token Error. redirect_uri required')
            return

        http = httpclient.AsyncHTTPClient()
        http.fetch(url_concat(self._OAUTH_ACCESS_TOKEN_URL, args),
                   callback=(yield gen.Callback('_RenrenGraphMixin.get_access_token')))
        response = yield gen.Wait('_RenrenGraphMixin.get_access_token')

        if response.error and not response.body:
            logging.warning("Error response %s fetching %s",
                            response.error, response.request.url)
            callback(None)
            return

        callback(response)
        return

    def _oauth_consumer_token(self):
        return dict(key=settings.networks['renren']['consumer_key'],
                    secret=settings.networks['renren']['consumer_secret'])


##########
# others #
##########


class FacebookAuthMixin(object):
    def authenticate_redirect(self, callback_uri=None, cancel_uri=None,
                              extended_permissions=None):
        """Authenticates/installs this app for the current user."""
        self.require_setting("facebook_api_key", "Facebook Connect")
        callback_uri = callback_uri or self.request.uri
        args = {
            "api_key": self.settings["facebook_api_key"],
            "v": "1.0",
            "fbconnect": "true",
            "display": "page",
            "next": urlparse.urljoin(self.request.full_url(), callback_uri),
            "return_session": "true",
        }
        if cancel_uri:
            args["cancel_url"] = urlparse.urljoin(
                self.request.full_url(), cancel_uri)
        if extended_permissions:
            if isinstance(extended_permissions, (unicode, bytes_type)):
                extended_permissions = [extended_permissions]
            args["req_perms"] = ",".join(extended_permissions)
        self.redirect("http://www.facebook.com/login.php?" +
                      urllib.urlencode(args))

    def authorize_redirect(self, extended_permissions, callback_uri=None,
                           cancel_uri=None):
        self.authenticate_redirect(callback_uri, cancel_uri,
                                   extended_permissions)

    def get_authenticated_user(self, callback):
        self.require_setting("facebook_api_key", "Facebook Connect")
        session = escape.json_decode(self.get_argument("session"))
        self.facebook_request(
            method="facebook.users.getInfo",
            callback=self.async_callback(
                self._on_get_user_info, callback, session),
            session_key=session["session_key"],
            uids=session["uid"],
            fields="uid,first_name,last_name,name,locale,pic_square,"
                   "profile_url,username")

    def facebook_request(self, method, callback, **args):
        self.require_setting("facebook_api_key", "Facebook Connect")
        self.require_setting("facebook_secret", "Facebook Connect")
        if not method.startswith("facebook."):
            method = "facebook." + method
        args["api_key"] = self.settings["facebook_api_key"]
        args["v"] = "1.0"
        args["method"] = method
        args["call_id"] = str(long(time.time() * 1e6))
        args["format"] = "json"
        args["sig"] = self._signature(args)
        url = "http://api.facebook.com/restserver.php?" + \
            urllib.urlencode(args)
        http = httpclient.AsyncHTTPClient()
        http.fetch(url, callback=self.async_callback(
            self._parse_response, callback))

    def _on_get_user_info(self, callback, session, users):
        if users is None:
            callback(None)
            return
        callback({
            "name": users[0]["name"],
            "first_name": users[0]["first_name"],
            "last_name": users[0]["last_name"],
            "uid": users[0]["uid"],
            "locale": users[0]["locale"],
            "pic_square": users[0]["pic_square"],
            "profile_url": users[0]["profile_url"],
            "username": users[0].get("username"),
            "session_key": session["session_key"],
            "session_expires": session.get("expires"),
        })

    def _parse_response(self, callback, response):
        if response.error:
            logging.warning("HTTP error from Facebook: %s", response.error)
            callback(None)
            return
        try:
            json = escape.json_decode(response.body)
        except Exception:
            logging.warning("Invalid JSON from Facebook: %r", response.body)
            callback(None)
            return
        if isinstance(json, dict) and json.get("error_code"):
            logging.warning("Facebook error: %d: %r", json["error_code"],
                            json.get("error_msg"))
            callback(None)
            return
        callback(json)

    def _signature(self, args):
        parts = ["%s=%s" % (n, args[n]) for n in sorted(args.keys())]
        body = "".join(parts) + self.settings["facebook_secret"]
        if isinstance(body, unicode):
            body = body.encode("utf-8")
        return hashlib.md5(body).hexdigest()
