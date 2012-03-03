#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Dependences:
#     * requests
#     * simplejson
#

import logging
test = logging.getLogger('test')
import urllib
import requests
import simplejson

_dict = lambda x: simplejson.loads(x, encoding='utf-8')
_json = lambda x: simplejson.dumps(x, ensure_ascii=False)


class FacebookAPIRequestError(Exception):
    pass


class Api(object):
    _API_PROTOCOL = 'https://'
    _API_DOMAIN = 'graph.facebook.com'

    def __init__(self,
                 app_id,
                 app_secret,
                 access_token):
        self.set_credential(app_id, app_secret, access_token)

    def set_credential(self, app_id, app_secret, access_token):
        self._app_id = app_id,
        self._app_secret = app_secret,
        self._access_token = access_token

    def _fetch(self, url):
        params = {
            'access_token': self._access_token,
        }
        url = self._API_PROTOCOL +\
              self._API_DOMAIN +\
              url + '?' +\
              urllib.urlencode(params)

        resp = requests.get(url)
        self._check_resp(resp)

        raw_data = resp.content
        try:
            data = _dict(raw_data)
        except:
            raise ValueError('Raw fetched data json parsing error')
        return data

    def _post(self, url, data):
        url = self._API_PROTOCOL +\
              self._API_DOMAIN + url
        data.update({'access_token': self._access_token})
        resp = requests.post(url, data=data)
        self._check_resp(resp)

    def _check_resp(self, resp):
        if resp.status_code > 399:
            raise FacebookAPIRequestError(resp)
        elif resp.status_code > 299:
            logging.warning('FacebookAPI request %s return code %s'\
                % (resp.request.url, resp.status_code))
        test.debug('url: %s, resp_body: %s' % (resp.request.url, resp.content))

    def GetFriends(self):
        return self._fetch('/me/friends')['data']

    def GetMeProfile(self):
        return self._fetch('/me')

    def GetMeStatuses(self):
        return self._fetch('/me/statuses')['data']

    def GetUserStatuses(self, id):
        return self._fetch('/%s/statuses' % id)['data']

    def PostStatus(self, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        assert isinstance(content, str), 'PostStatus content must be str, not %s' % type(content)
        self._post('/me/feed', {
            'message': content
        })
