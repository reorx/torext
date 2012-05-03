#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
from random import choice, randint
from hashlib import md5

CHARS = string.letters + string.digits


def md5_string(s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    return md5(s).hexdigest()


def longer_int_id(id):
    length = 8  # if id shorter than this
    id_len = len(str(id))
    if not id_len > length:
        nid = choice('123456789') +\
              ''.join([choice(string.digits) for i in range(length - 1 - id_len)]) + str(id)
    else:
        nid = id
    return nid


def random_string(length=10):
    return ''.join([choice(CHARS) for i in range(length)])


def random_list_item(l):
    return l[randint(0, len(l) - 1)]


def salt_md5(s):
    return md5_string(s + random_string(5))


def random_salt_md5(s):
    HEXCHAR = '0123456789ABCDEF'
    s = md5_string(s)
    p1 = s[:2]
    p2 = s[2:6]
    p3 = s[6:14]
    p4 = s[14:30]
    p5 = s[30:]
    ss = p1 + choice(HEXCHAR[0:4]) +\
            p2 + choice(HEXCHAR[4:8]) +\
            p3 + choice(HEXCHAR[8:12]) +\
            p4 + choice(HEXCHAR[12:16]) +\
            p5
    return ss.lower()


def generate_cookie_secret():
    import uuid
    import base64
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
