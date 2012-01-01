"""
Dependences:
    * python-requests
    * simplejson
"""
import urllib
import requests
import simplejson

_dict = lambda x: simplejson.loads(x, encoding='utf-8')
_json = lambda x: simplejson.dumps(x, ensure_ascii=False, cls=DateTimeJSONEncoder)

class Api(object):
    _API_PROTOCOL = 'https://'
    _API_DOMAIN = 'graph.facebook.com'

    def __init__(self,
                 app_id=None,
                 app_secret=None,
                 access_token=None):
        if not app_id or not app_secret:
            app_id = FB_APP_ID
            app_secret = FB_APP_SECRET
        if not access_token:
            raise ValueError

        self.set_credential(app_id, app_secret, access_token)

    def set_credential(self, app_id, app_secret, access_token):
        self._app_id = app_id,
        self._app_secret = app_secret,
        self._access_token = access_token

    def _fetch(self, url):
        url_params = {
            'access_token': self._access_token,
        }
        url = self._API_PROTOCOL +\
              self._API_DOMAIN +\
              url + '?' +\
              urllib.urlencode(url_params)

        resp = requests.get(url)
        print url
        raw_data = resp.content
        print raw_data
        #try:
        data = _dict(raw_data)
        #except:
            #raise FacebookParseError('JSON Handle Error')
        return data

    def _post(self, url, data):
        #req_url_headers = { 'access_token': self._access_token}
        url = self._API_PROTOCOL +\
              self._API_DOMAIN + url
        data.update({'access_token': self._access_token})

        resp = requests.post(url, data=data)
        return resp

    def GetFriends(self):
        data = self._fetch('/me/friends')
        return data['data']

    def GetMeProfile(self):
        data = self._fetch('/me')
        return data

    def GetMeStatuses(self):
        data = self._fetch('/me/statuses')
        return data['data']

    def GetUserStatuses(self, id):
        url = '/%s/statuses' % id
        data = self._fetch(url)
        return data['data']

    def PostStatus(self, content):
        url = '/me/feed'
        print 'facebook post content: ', content, type(content)
        content = content.encode('utf-8')
        postData = dict(
            message = content
        )
        resp = self._post(url, postData)

class FacebookParseError(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg
