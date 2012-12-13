#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import logging
import datetime
from hashlib import md5
from torext.errors import ValidationError
from bson.objectid import ObjectId


DEFAULT_TYPE_VALUE = {
    int: int,
    float: float,
    str: str,
    unicode: unicode,
    # bool() == False
    bool: bool,
    list: list,
    dict: dict,
    # to ensure every objectid is generated seperately
    #ObjectId: lambda: ObjectId(),
    ObjectId: ObjectId,
    datetime.datetime: lambda: datetime.datetime.now()
}


def check_struct(struct):
    """
    ensure every key in struct is of str type
    """
    for k, v in struct.iteritems():
        # check key to be str
        if not isinstance(k, str):
            raise StructDefineError('key "%s" is not a str' % k)

        # NOTE isinstance(dict, dict) is False
        if isinstance(v, dict):
            check_struct(v)

        elif isinstance(v, list):
            if len(v) > 1:
                raise StructDefineError('value "%s" can at most contains one item' % v)
            elif len(v) == 1:
                v_item = v[0]
                if isinstance(v_item, dict):
                    check_struct(v_item)
                else:
                    if not v_item in Struct.ALLOW_TYPES:
                        raise StructDefineError('value "%s" in list '
                                                'is neither one of Struct.ALLOW_TYPES '
                                                'nor instance of dict' % v_item)

        # check value to be type in `ALLOW_TYPES` if not instance of dict or list
        else:
            if not v in Struct.ALLOW_TYPES:
                raise StructDefineError('value "%s" is not one of Struct.ALLOW_TYPES' % v)


def validate_dict(doc, struct, allow_None_types=[], brother_types=[]):
    """
    Validate a dict from the defined structure.

    Thoughts:
        In the inner function `recurse_check`, treat `st` as basement,
        iter every key and value to see if key-value exists and fits in `o`,

        during the iteration, when list is encountered, check if the value of
        the same key in `o` is list, then iter the list value from `o` ( not `st`),
        and pass the first item of `st`s list value as `st` argument to the
        newly running `recurse_check`.

    This function can strictly check that if every key in `struct`
    is the same as in `doc`, that is, `struct` -> `doc`, so this example will not pass:
    >>> doc = {
    ...     'a': '',
    ...     'b': [
    ...         {
    ...             'c': 0
    ...         }
    ...     ]
    ... }
    >>> struct = {
    ...     'a': str,
    ...     'b': [
    ...         {
    ...             'c': int
    ...             'd': str
    ...         }
    ...     ]
    ... }
    >>> validate_dict(doc, struct)

    Traceback (most recent call last):
        raise ValidationError('%s: key %s not in %s' % (ck, k, o))
    torext.errors.ValidationError: $.b.[0]: key d not in {'c': 0}

    Because we don't see if every key in `doc` is in `struct` reversely,
    this example will just pass:
    >>> doc = {
    ...     'a': '',
    ...     'b': [
    ...         {
    ...             'c': 0
    ...             'd': '',
    ...             'e': 'i am e'
    ...         }
    ...     ],
    ...     'f': 'i am f'
    ... }
    >>> struct = {
    ...     'a': str,
    ...     'b': [
    ...         {
    ...             'c': int
    ...             'd': str
    ...         }
    ...     ]
    ... }
    >>> validate_dict(doc, struct)
    """
    logging.debug('------call validate_dict()')

    assert isinstance(doc, dict), 'doc must be dict'
    assert isinstance(struct, dict), 'struct must be dict'
    check_struct(struct)

    def recurse_check(st, o, ck):
        # `st` means struct, it could be a type
        # `o`  means object to be validate
        # `ck` means current key
        # `nk` means next key
        # `bv` means bottom value

        if st in Struct.ALLOW_TYPES:
            typ = st
        else:
            # list or dict
            typ = type(st)
        logging.debug('@ %s\ndefine: %s\nobj   : %s %s' % (ck, typ, type(o), o))

        if not isinstance(o, typ):
            _pass = False
            if o is None:
                if typ in allow_None_types:
                    logging.debug('allowing condition: %s can be None' % ck)
                    _pass = True
            else:
                for bro in brother_types:
                    if typ in bro and isinstance(o, bro):
                        logging.debug('allowing condition: (%s, %s) in brother_types' % (type(o), typ))
                        _pass = True
                        break

            if not _pass:
                raise ValidationError(
                    'Position(%s): type "%s" should be "%s", value: "%s"' % (ck, type(o), typ, o))

        logging.debug('---')

        # recurse down step
        if isinstance(st, dict):
            for k, nst in st.iteritems():
                if not k in o:
                    raise ValidationError('Position(%s): key "%s" not in "%s"' % ((ck is None) or '*TOP*', k, o))
                if ck is None:
                    nk = k
                else:
                    nk = ck + '.' + k
                recurse_check(nst, o[k], nk)

        elif isinstance(st, list) and len(st) == 1:
            # NOTE currently, redundancy validations, which may occured on list,
            # could not be reduced, because of the unperfect mechanism ..
            # nk = ck + '.*'
            nst = st[0]
            for loop, i in enumerate(o):
                nk = '%s.[%s]' % (ck, loop)
                recurse_check(nst, i, nk)

    recurse_check(struct, doc, None)
    logging.debug('------validation all passed !')


def build_dict(struct, **default):
    """
    DICT !!
    WILL NEVER HANDLE ANY THING IN LIST !!

    build a dict from struct,
    struct & the result can only be dict

    NOTE
     * inner list will be ignored (build to [])
     * KeyError will be raised if not all dot_keys in default are properly set
    """
    assert isinstance(struct, dict), 'struct must be dict'
    # to prevent changes on default
    if default:
        _default = copy.deepcopy(default)
    else:
        _default = {}

    def recurse_struct(st, pk):
        cd = {}

        for k, v in st.iteritems():
            if pk is None:
                ck = k
            else:
                ck = pk + '.' + k

            # if dot_key is found in default, stop recurse and set value immediatelly
            # this may make the dict structure broken (not valid with struct),
            # so a validate() will do at following
            if ck in _default:
                kv = _default.pop(ck)
            else:
                if isinstance(v, dict):
                    kv = recurse_struct(v, ck)
                else:
                    if isinstance(v, list):
                        v = list
                    assert isinstance(v, type), '%s %s must be <type type>' % (ck, v)

                    kv = DEFAULT_TYPE_VALUE.get(v, lambda: None)()

            cd[k] = kv
            logging.debug('build: $.%s -> %s' % (ck, kv))

        return cd

    built = recurse_struct(struct, None)

    if len(_default.keys()) > 0:
        raise KeyError('Assignments of default value `%s` failed' % _default)

    return built


def _key_rule(k):
    if k.startswith('[') and k.endswith(']'):
        k = int(k[1:-1])
    return k


def retrieve_dict(doc, dot_key):
    """
    Could index value out by dot_key like this:
        foo.bar.[0].player

    """
    def recurse_dict(d, klist):
        try:
            k = klist.pop(0)
        except IndexError:
            return d

        d = d[_key_rule(k)]
        return recurse_dict(d, klist)

    spKeys = dot_key.split('.')

    return recurse_dict(doc, spKeys)


def map_dict(o):
    def recurse_doc(mapping, d, pk):
        if isinstance(d, dict):
            for k, v in d.iteritems():
                if pk is None:
                    ck = k
                else:
                    ck = pk + '.' + k
                recurse_doc(mapping, v, ck)
        elif isinstance(d, list):
            for loop, i in enumerate(d):
                ck = pk + '.' + '[%s]' % loop
                recurse_doc(mapping, i, ck)
        else:
            mapping[pk] = d
        return mapping

    return recurse_doc({}, o, None)


def hash_dict(o):
    """
    As dict is not hashable, this function is to generate a hash string
    from a dict unnormally, use every key & value of the dict,
    join then up and compute its md5 value.
    """
    seprator = '\n'
    mapping = map_dict(o)
    keys = mapping.keys()

    # get rid the random effect of dict keys, to ensure same dict will result to same value.
    keys.sort()

    string = seprator.join(['%s:%s' % (k, mapping[k]) for k in keys])
    return md5(string).hexdigest()


class GenCaller(object):
    def __get__(self, ins, owner):
        return Gen(owner)


class Gen(object):
    def __init__(self, struct_class):
        self.__struct_class = struct_class
        self.__dot_key = None

    def __get_struct(self):
        """
        if the struct indexed is a list, return its first item

        the result can be anything in DEFAULT_TYPE_VALUE except 'list'

        note that '__' is used for naming attributes to avoid conflicts
        """
        def recurse_struct(st, klist):
            if isinstance(st, list):
                st = st[0]
            try:
                k = klist.pop(0)
            except IndexError:
                return st
            st = st[k]
            return recurse_struct(st, klist)

        keys = self.__dot_key.split('.')
        return recurse_struct(self.__struct_class.struct, keys)

    def __call__(self, *args, **kwgs):
        struct = self.__get_struct()
        #logging.debug('%s index struct: %s' % (self.__dot_key, struct))
        if isinstance(struct, dict):
            return build_dict(struct, *args, **kwgs)
        else:
            return DEFAULT_TYPE_VALUE.get(struct, lambda: None)()

    def __getattr__(self, key):
        if self.__dot_key is None:
            self.__dot_key = key
        else:
            self.__dot_key += '.' + key
        return self


class StructDefineError(Exception):
    pass


class Struct(object):
    """
    Struct is designed for validate dict that will be stored into mongodb,
    so it will follow mongodb documents' standard on namespace, type, and value.

    Notations:
        * key must be str type
        * only allow these types (explained in python thought):
            1. type(None)
            2. bool
            3. int/float
            4. str/unicode
            5. list
            6. dict
            7. ObjectId
    """
    ALLOW_TYPES = (
        #type(None),  # ? will it be used ?
        bool,
        int, float,
        str, unicode,
        list,
        dict,
        ObjectId,
        datetime.datetime,
    )

    def __init__(self, struct):
        assert isinstance(struct, dict), 'struct must be dict type'

        check_struct(struct)
        self._struct = struct

    def __get__(self, ins, owner):
        return self._struct


class StructuredDict(dict):
    """
    Philosophy:
        1. instance has the same keys, no less, no more, with defined struct.
        2. when initializing instance, if no default value input, key-value will be auto created.
        3. when auto creating and validating, if the key isn't in `force_type`, None will be allowed.
        4. no unique judgements
        5. keys not in struct could not be read or set.
        6. validator is not included in concept, it should be outside of structure.

    TODO.
        * auto_fix for raw doc in mongodb to fit struct (always use in developing at which time struct changes frequently)

    NOTE.
        * '' and None. When a key has no input default value, it will be asigned as None
          unless it's in strict_indexes
        * keys in struct must be str

    Usage::

        # define a new struct:
        >>> class SomeStruct(StructuredDict):
        ...     struct = {
        ...         'id': ObjectId,
        ...         'name': str,
        ...         'description': unicode,
        ...         'contributers': [
        ...             {
        ...                 'name': str,
        ...                 'rate': float,
        ...                 'hangon': bool,
        ..              }
        ...         ],
        ...         'flag': list,
        ...     }
        ...
        ...     default_values = {
        ...         'flag': 'fuck-you',
        ...     }
        ...
        ...     allow_None_types = [
        ...         str,
        ...     ]
        ...

        # build a pure instance:
        >>> doc = SomeStruct.build_instance()

        # or with some default values
        >>> doc = SomeStruct.build_instance(default={
        ...     'name': 'Just Bili.H',
        ... })

        then you can do some thing with it
    """
    gen = GenCaller()

    allow_None_types = [str, unicode, ]

    brother_types = [
        (str, unicode),
        (int, long),
    ]

    @classmethod
    def build_instance(cls, *args, **kwgs):
        """
        use build_dict() to create a dict object,
        return an instance of cls from that dict object.
        """
        ins = cls(build_dict(cls.struct, *args, **kwgs))
        ins.validate()
        return ins

    def validate(self):
        cls = self.__class__
        validate_dict(self, cls.struct,
                      allow_None_types=cls.allow_None_types,
                      brother_types=cls.brother_types)

    def retrieval_get(self, dot_key):
        """
        raise IndexError or KeyError if can not get

        Example:
            'menu.file.name'
            'menu.ps.[0].title'
        """
        return retrieve_dict(dict(self), dot_key)

    def retrieval_set(self, dot_key, value):
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        last = self.retrieval_get('.'.join(keys))
        last[_key_rule(last_key)] = value

    def retrieval_del(self, dot_key):
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        last = self.retrieval_get('.'.join(keys))
        del last[_key_rule(last_key)]

    def _pprint(self):
        from torext.utils import pprint
        pprint(dict(self))

    def __str__(self):
        s = '<%s of StructuredDict: %s>' %\
            (self.__class__.__name__,
             ','.join(['%s=%s' % (k, v) for k, v in self.iteritems()]))
        return s
