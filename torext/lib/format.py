#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import simplejson as pyjson
from bson.objectid import ObjectId


class CustomJSONEncoder(pyjson.JSONEncoder):
    """
    copy from django.core.serializers.json
    """
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, ObjectId):
            return o.__str__()
        elif isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        else:
            return super(CustomJSONEncoder, self).default(o)


def _dict(json):
    return pyjson.loads(json, encoding='utf-8')


def _json(dic):
    return pyjson.dumps(dic, ensure_ascii=False, cls=CustomJSONEncoder)


def force_int(value, desire=0, limit=100):
    try:
        value = int(value)
    except:
        value = desire
    if value > limit:
        return limit / 2
    return value


def timesince(time):
    import datetime
    if not isinstance(time, datetime.datetime):
        return None
    now = datetime.datetime.utcnow()
    delta = now - time
    if not delta.days:
        if delta.seconds / 3600:
            return '{0} hours ago'.format(delta.seconds / 3600)
        return '{0} minutes ago'.format(delta.seconds / 60)
    if delta.days / 365:
        return '{0} years ago'.format(delta.days / 365)
    if delta.days / 30:
        return '{0} months ago'.format(delta.days / 30)
    return '{0} days ago'.format(delta.days)


_UTF8_TYPES = (bytes, type(None))


def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    assert isinstance(value, unicode)
    return value.encode("utf-8")


def uni(s):
    assert s is not None, 'uni() require input not None'
    if isinstance(s, str):
        s = s.decode('utf-8')
    return s
