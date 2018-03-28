import sys


PY3 = sys.version_info.major == 3
PY2 = sys.version_info.major == 2


if PY2:
    from urllib import urlencode, quote
    from urlparse import urljoin
    import httplib
    from Cookie import SimpleCookie
    def unicode_(s, *args):
        return unicode(s, *args)
    def decode_(s, *args):
        s.decode(*args)
    def bytes_(s):
        return s
    def str_(s):
        return s
else:
    from urllib.parse import urlencode, quote, urljoin
    import http.client as httplib
    from http.cookies import SimpleCookie
    def unicode_(s, *args):
        return s
    def decode_(s, *args):
        return s
    def bytes_(s):
        return s.encode('utf8')
    def str_(s):
        return s.decode('utf8')
