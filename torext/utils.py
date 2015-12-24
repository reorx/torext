#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import functools


import json

try:
    from tornado.util import raise_exc_info
except ImportError:
    def raise_exc_info(exc_info):
        """Re-raise an exception (with original traceback) from an exc_info tuple.

        The argument is a ``(type, value, traceback)`` tuple as returned by
        `sys.exc_info`.
        """
        # 2to3 isn't smart enough to convert three-argument raise
        # statements correctly in some cases.
        if isinstance(exc_info[1], exc_info[0]):
            raise exc_info[1], None, exc_info[2]
            # After 2to3: raise exc_info[1].with_traceback(exc_info[2])
        else:
            # I think this branch is only taken for string exceptions,
            # which were removed in Python 2.6.
            raise exc_info[0], exc_info[1], exc_info[2]
            # After 2to3: raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])


def generate_cookie_secret():
    import uuid
    import base64
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


json_decode = functools.partial(json.loads, encoding='utf-8')


json_encode = functools.partial(json.dumps, ensure_ascii=False)


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


def pprint(o):
    import pprint
    pprinter = pprint.PrettyPrinter(indent=4)
    pprinter.pprint(o)


class SingletonMixin(object):
    """Globally hold one instance class

    Usage:
    >>> class SpecObject(SingletonMixin):
    ...     pass

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
            raise AttributeError('Has no attribute %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return '<ObjectDict %s >' % dict(self)


# def import_underpath_module(path, name):
#     """
#     arguments::
#     :name :: note that name do not contain `.py` at the end
#     """
#     importer = pkgutil.get_importer(path)
#     logging.debug('loading handler module: ' + name)
#     return importer.find_module(name).load_module(name)
#
#
# def autoload_submodules(dirpath):
#     """Load submodules by dirpath
#     NOTE. ignore packages
#     """
#     import pkgutil
#     importer = pkgutil.get_importer(dirpath)
#     return (importer.find_module(name).load_module(name)
#             for name, is_pkg in importer.iter_modules())


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

    Usage:
    >>> epoll_module = import_module('tornado.platform.epoll')
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


_abspath = lambda x: os.path.abspath(x)
_join = lambda x, y: os.path.join(x, y)


def add_to_syspath(pth, relative_to=None):
    if relative_to:
        pth = _join(relative_to, pth)
    if _abspath(pth) in [_abspath(i) for i in sys.path]:
        print 'path %s is in sys.path, pass' % pth
    else:
        print 'add path %s to sys.path' % pth
        sys.path.insert(0, pth)


def start_shell(extra_vars=None):
    import code
    import rlcompleter
    import readline

    class CustomCompleter(rlcompleter.Completer):
        def complete(self, text, state):
            if text == "":
                # you could  replace \t to 4 or 8 spaces if you prefer indent via spaces
                return ['    ', None][state]
            else:
                # return rlcompleter.Completer.complete(self, text, state)
                return super(CustomCompleter, self).complete(text, state)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(CustomCompleter().complete)

    import __main__
    if extra_vars:
        __main__.__dict__.update(
            dict((k, v) for k, v in extra_vars.iteritems() if not k.startswith('__')))

    # As completer class search complement variables in `__main__.__dict__`
    # (`self.namespace = __main__.__dict__` in 'rlcompleter.Completer.complete'),
    # and the code is executed by `exec code in self.locals`
    # (in `code.InteractiveInterpreter.runcode`),
    # `__main__.__dict__` must be used as the local variables scope,
    # not `globals()`, `locals()` or any other dict,
    # (`__main__` module is explained here: http://docs.python.org/2/library/__main__.html)
    shell = code.InteractiveConsole(__main__.__dict__)
    shell.interact()
    # code.interact(local=__main__.__dict__)


def fix_request_arguments(arguments):
    return dict((k, v[0]) for k, v in arguments.iteritems())


class LocalProxy(object):
    """Acts as a proxy for a werkzeug local.  Forwards all operations to
    a proxied object.  The only operations not supported for forwarding
    are right handed operands and any kind of assignment.
    Example usage::
        from werkzeug.local import Local
        l = Local()
        # these are proxies
        request = l('request')
        user = l('user')
        from werkzeug.local import LocalStack
        _response_local = LocalStack()
        # this is a proxy
        response = _response_local()
    Whenever something is bound to l.user / l.request the proxy objects
    will forward all operations.  If no object is bound a :exc:`RuntimeError`
    will be raised.
    To create proxies to :class:`Local` or :class:`LocalStack` objects,
    call the object as shown above.  If you want to have a proxy to an
    object looked up by a function, you can (as of Werkzeug 0.6.1) pass
    a function to the :class:`LocalProxy` constructor::
        session = LocalProxy(lambda: get_current_request().session)
    .. versionchanged:: 0.6.1
       The class can be instanciated with a callable as well now.
    """
    __slots__ = ('__local', '__dict__', '__name__')

    def __init__(self, local, name=None):
        object.__setattr__(self, '_LocalProxy__local', local)
        object.__setattr__(self, '__name__', name)

    def get_current_object(self):
        """Return the current object.  This is useful if you want the real
        object behind the proxy at a time for performance reasons or because
        you want to pass the object into a different context.
        """
        if not hasattr(self.__local, '__release_local__'):
            return self.__local()
        try:
            return getattr(self.__local, self.__name__)
        except AttributeError:
            raise RuntimeError('no object bound to %s' % self.__name__)

    @property
    def __dict__(self):
        try:
            return self.get_current_object().__dict__
        except RuntimeError:
            raise AttributeError('__dict__')

    def __repr__(self):
        try:
            obj = self.get_current_object()
        except RuntimeError:
            return '<%s unbound>' % self.__class__.__name__
        return repr(obj)

    def __bool__(self):
        try:
            return bool(self.get_current_object())
        except RuntimeError:
            return False

    def __unicode__(self):
        try:
            return unicode(self.get_current_object())
        except RuntimeError:
            return repr(self)

    def __dir__(self):
        try:
            return dir(self.get_current_object())
        except RuntimeError:
            return []

    def __getattr__(self, name):
        if name == '__members__':
            return dir(self.get_current_object())
        return getattr(self.get_current_object(), name)

    def __setitem__(self, key, value):
        self.get_current_object()[key] = value

    def __delitem__(self, key):
        del self.get_current_object()[key]

    __getslice__ = lambda x, i, j: x.get_current_object()[i:j]

    def __setslice__(self, i, j, seq):
        self.get_current_object()[i:j] = seq

    def __delslice__(self, i, j):
        del self.get_current_object()[i:j]

    __setattr__ = lambda x, n, v: setattr(x.get_current_object(), n, v)
    __delattr__ = lambda x, n: delattr(x.get_current_object(), n)
    __str__ = lambda x: str(x.get_current_object())
    __lt__ = lambda x, o: x.get_current_object() < o
    __le__ = lambda x, o: x.get_current_object() <= o
    __eq__ = lambda x, o: x.get_current_object() == o
    __ne__ = lambda x, o: x.get_current_object() != o
    __gt__ = lambda x, o: x.get_current_object() > o
    __ge__ = lambda x, o: x.get_current_object() >= o
    __cmp__ = lambda x, o: cmp(x.get_current_object(), o)
    __hash__ = lambda x: hash(x.get_current_object())
    __call__ = lambda x, *a, **kw: x.get_current_object()(*a, **kw)
    __len__ = lambda x: len(x.get_current_object())
    __getitem__ = lambda x, i: x.get_current_object()[i]
    __iter__ = lambda x: iter(x.get_current_object())
    __contains__ = lambda x, i: i in x.get_current_object()
    __add__ = lambda x, o: x.get_current_object() + o
    __sub__ = lambda x, o: x.get_current_object() - o
    __mul__ = lambda x, o: x.get_current_object() * o
    __floordiv__ = lambda x, o: x.get_current_object() // o
    __mod__ = lambda x, o: x.get_current_object() % o
    __divmod__ = lambda x, o: x.get_current_object().__divmod__(o)
    __pow__ = lambda x, o: x.get_current_object() ** o
    __lshift__ = lambda x, o: x.get_current_object() << o
    __rshift__ = lambda x, o: x.get_current_object() >> o
    __and__ = lambda x, o: x.get_current_object() & o
    __xor__ = lambda x, o: x.get_current_object() ^ o
    __or__ = lambda x, o: x.get_current_object() | o
    __div__ = lambda x, o: x.get_current_object().__div__(o)
    __truediv__ = lambda x, o: x.get_current_object().__truediv__(o)
    __neg__ = lambda x: -(x.get_current_object())
    __pos__ = lambda x: +(x.get_current_object())
    __abs__ = lambda x: abs(x.get_current_object())
    __invert__ = lambda x: ~(x.get_current_object())
    __complex__ = lambda x: complex(x.get_current_object())
    __int__ = lambda x: int(x.get_current_object())
    __long__ = lambda x: long(x.get_current_object())
    __float__ = lambda x: float(x.get_current_object())
    __oct__ = lambda x: oct(x.get_current_object())
    __hex__ = lambda x: hex(x.get_current_object())
    __index__ = lambda x: x.get_current_object().__index__()
    __coerce__ = lambda x, o: x.get_current_object().__coerce__(x, o)
    __enter__ = lambda x: x.get_current_object().__enter__()
    __exit__ = lambda x, *a, **kw: x.get_current_object().__exit__(*a, **kw)
    __radd__ = lambda x, o: o + x.get_current_object()
    __rsub__ = lambda x, o: o - x.get_current_object()
    __rmul__ = lambda x, o: o * x.get_current_object()
    __rdiv__ = lambda x, o: o / x.get_current_object()
    __rtruediv__ = lambda x, o: x.get_current_object().__rtruediv__(o)
    __rfloordiv__ = lambda x, o: o // x.get_current_object()
    __rmod__ = lambda x, o: o % x.get_current_object()
    __rdivmod__ = lambda x, o: x.get_current_object().__rdivmod__(o)
