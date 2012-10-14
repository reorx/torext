#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import string
import pkgutil
import logging
import datetime
from hashlib import md5
from random import choice, randint
from bson.objectid import ObjectId

_abspath = lambda x: os.path.abspath(x)
_join = lambda x, y: os.path.join(x, y)
_abs_join = lambda x, y: _abspath(_join(x, y))

try:
    import simplejson as pyjson
except ImportError:
    import json as pyjson

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


def timesince(t):
    if not isinstance(t, datetime.datetime):
        raise TypeError('Time should be instance of datetime.datetime')
    now = datetime.datetime.utcnow()
    delta = now - t
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


def pprint(o):
    import pprint as PPrint
    pprinter = PPrint.PrettyPrinter(indent=4)
    pprinter.pprint(o)


class SingletonMixin(object):
    """Globally hold one instance class

    Usage::
        >>> class SpecObject(OneInstanceImp):
        >>>     pass

        >>> ins = SpecObject.instance()
    """
    @classmethod
    def instance(cls, *args, **kwgs):
        """Will be the only instance"""
        if not hasattr(cls, "_instance"):
            cls._instance = cls(*args, **kwgs)
        return cls._instance


def split_kwargs(kwgs_tuple, kwgs):
    _kwgs = {}
    for i in kwgs_tuple:
        if i in kwgs:
            _kwgs[i] = kwgs.pop(i)
    return _kwgs


class ObjectDict(dict):
    """
    retrieve value of dict in dot style
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('has no attribute %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return '<ObjectDict %s >' % dict(self)


def import_underpath_module(path, name):
    """
    arguments::
    :name :: note that name do not contain `.py` at the end
    """
    importer = pkgutil.get_importer(path)
    logging.debug('loading handler module: ' + name)
    return importer.find_module(name).load_module(name)


def autoload_submodules(dirpath):
    """Load submodules by dirpath
    NOTE. ignore packages
    """
    import pkgutil
    importer = pkgutil.get_importer(dirpath)
    return (importer.find_module(name).load_module(name)
            for name, is_pkg in importer.iter_modules())


######################################
# borrow from django.utils.importlib #
######################################

# Taken from Python 2.7 with permission from/by the original author.

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level\
                package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]


def start_shell(local_vars={}):
    import os
    import code
    import readline
    import rlcompleter

    class irlcompleter(rlcompleter.Completer):
        def complete(self, text, state):
            if text == "":
                #you could  replace \t to 4 or 8 spaces if you prefer indent via spaces
                return ['    ', None][state]
            else:
                return rlcompleter.Completer.complete(self, text, state)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(irlcompleter().complete)

    pythonrc = os.environ.get("PYTHONSTARTUP")
    if pythonrc and os.path.isfile(pythonrc):
        try:
            execfile(pythonrc)
        except NameError:
            pass
    # This will import .pythonrc.py as a side-effect
    import user
    user.__file__

    _locals = locals()
    for i in _locals:
        if not i.startswith('__') and i != 'local_vars':
            local_vars[i] = _locals[i]
    local_vars.update({
        '__name__': '__main__',
        '__package__': None,
        '__doc__': None,
    })

    # TODO problem: could not complete exising vars.

    code.interact(local=local_vars)
