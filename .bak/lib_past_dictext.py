#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Philosophy:
    * `struct` is straight, this is of top importance !
      because if you want your struct, compatible with
      several objects, why not define by their intersection ?

    * types in `struct` should be simple, cover bottom basics,
      struct can only be dict: cause most times list needs validation are list contain items of dict.
      structural types   : dict, list
      frank types        : str, unicode, int, bool
      no limitation type : None

    * complex type or custom type is unnesessary,,
      `validators` can handle those things.

Example:
struct = {
    'name': str,
    'nature': {
        'rtrn': int
    },
    'people': [str],
    'disks': [
        {'title': str }
    ]
}

doc_keys = [
    '$'
    '$.name'
    '$.nature'
    '$.nature.rtrn'
    '$.people'
    '$.people.*'
    '$.disks'
    '$.disks.*',
    '$.disks.*.title'
]

data = {
    'name': 'reorx',
    'nature': {
        'rtrn': 100
    },
    'people': ['aoyi', 'utada'],
    'disks': [
        {'title': 's', },
        {'title': 'DATA'}
    ]
}
"""

import logging
from hashlib import md5
from pymongo.objectid import ObjectId
from torext.errors import ValidationError


test = logging.getLogger('test')
test.setLevel(logging.INFO)


DEFAULT_TYPE_VALUE = {
    int: lambda: 0,
    float: lambda: 0.0,
    str: lambda: None,  # NOTE really None ?
    unicode: lambda: None,  # NOTE think later, dangerous(easy to cause problem) !
    bool: lambda: True,
    list: lambda: [],
    dict: lambda: {},
    ObjectId: lambda: ObjectId()
}


class GenCaller(object):
    def __get__(self, ins, owner):
        return Gen(owner)


class StructuredDict(dict):
    """
    Philosophy.
        1. instance has the same keys, no less, no more, with defined struct.
        2. when initializing instance, if no default value input, key-value will be auto created.
        3. when auto creating and validating, if key isn't in `force_type`, None will be allowed.
        4. no unique judgements
        5. keys not in struct could not be read or set.
        6. validator is not included in concept, it should be outside of structure.

    TODO.
        * auto_fix for raw doc in mongodb to fit struct (always use in developing at which time struct changes frequently)

    NOTE.
        * '' and None. When a key has no input default value, it will be asigned as None
          unless it's in strict_indexes

    >>> class SomeStruct(StructuredDict):
    ...     struct = {
    ...         'id': ObjectId,
    ...         'name': str,
    ...         'description': str,
    ...         'flag': str,
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
    """
    gen = GenCaller()

    allow_None_types = [str, unicode, ]

    brother_types = [
        (str, unicode),
        (int, long),
    ]

    @classmethod
    def validate(cls, doc):
        validate_dict(doc, cls.struct, allow_nones=cls.allow_None_types)

    @classmethod
    def build_instance(cls, **kwgs):
        kwgs['dict_class'] = cls
        instance = build_dict(cls.struct, **kwgs)
        # return instance

        try:
            validate_dict(instance, cls.struct, cls.allow_None_types)
        except ValidationError, e:
            raise ValidationError('validate error in build_dict(), may be\
                    dict structure is broken by default ? | %s' % e)
        return instance


class Gen(object):
    def __init__(self, structObj):
        self.__structObj = structObj
        self.__dot_key = '$'

    def __index_struct(self):
        """
        if the struct indexed is a list, return its first item
        """
        def recurse_st(st, klist):
            try:
                k = klist.pop(0)
            except:
                if isinstance(st, list):
                    return st[0]
                return st
            st = st[k]
            return recurse_st(st, klist)
        spKeys = self.__dot_key.split('.')[1:]
        return recurse_st(self.__structObj.struct, spKeys)

    def __call__(self, **kwgs):
        struct = self.__index_struct()
        # now struct can only be: dict_ins, int*, str*, bool
        if isinstance(struct, dict):
            return build_dict(struct, **kwgs)
        else:
            if struct in DEFAULT_TYPE_VALUE:
                return DEFAULT_TYPE_VALUE[struct]()
            else:
                return None

    def __getattr__(self, key):
        self.__dot_key = '%s.%s' % (self.__dot_key, key)
        return self


def validate_dict(doc, struct, allow_nones=[], brother_types=[]):
    def iter_struct(st, ck):
        # `ck` means current key
        test.debug('@ ' + ck)
        if isinstance(st, type):
            typ = st
        else:
            typ = type(st)
        test.debug('define: %s' % typ)

        # index in doc
        try:
            o = index_dict(doc, ck)
        except KeyError:
            raise ValidationError(ck + ' could not index out')

        test.debug('obj: %s %s' % (o, type(o)))

        # so that if o is an empty iterable (originally list), this step will pass
        if not isinstance(o, tuple):
            o = (o, )

        for i in o:
            test.debug('item: %s %s' % (i, type(i)))
            if not isinstance(i, typ):
                if i is None and typ in allow_nones:
                    test.debug('allowing condition: %s can be None' % ck)
                    continue

                _brother_types_pass = False
                for bro in brother_types:
                    if type(i) in bro and typ in bro:
                        test.debug('allowing condition: (%s, %s) in brother_types' % (type(i), typ))
                        _brother_types_pass = True
                        continue
                if _brother_types_pass:
                    continue
                # if (type(i) is str and typ is unicode) or\
                #     (type(i) is unicode and typ is str):
                #     # NOTE temporarily let unicode and str compatable
                #     continue
                # if type(i) is long and typ is int:
                #     continue
                raise ValidationError(
                    '{0}: invalid {1}, should be {2}, value: {3}'.format(ck, type(i), typ, repr(i)))

        test.debug('---')
        # iter down step
        if isinstance(st, dict):
            for k, v in st.iteritems():
                assert not isinstance(k, type), 'struct key must not be type object'
                nk = ck + '.' + k
                iter_struct(v, nk)
        elif isinstance(st, list):
            # NOTE currently, redundancy validations, which maily occured on list,
            # could not be reduced, because of the unperfect mechanism ..
            nk = ck + '.*'
            iter_struct(st[0], nk)
        else:  # isinstance(st, type)
            return
    iter_struct(struct, '$')
    test.debug('all passed !')


def build_dict(struct, default={}, dict_class=dict):
    """
    build a dict from struct,
    struct & the result can only be dict

    NOTE
     * inner list will be passed (build to [])
     * KeyError will be raised if not all dot_keys in default are properly set
    """
    def recurse_struct(dst, ck):
        cd = dict_class()
        for k, v in dst.iteritems():
            if not ck:
                nk = k
            else:
                nk = ck + '.' + k
            test.debug('set value to: ' + nk)

            # if dot_key is find in default, stop recurse and set value immediatelly
            # this may make the dict structure broken (not valid with struct),
            # so a validate() will do at following
            if nk in default:
                kv = default.pop(nk)
            else:
                if type(v) is dict:
                    kv = recurse_struct(v, nk)
                else:
                    # get type-default value
                    # fix ObjectId judge
                    if not v is ObjectId and not isinstance(v, type):
                        v = type(v)
                    if v in DEFAULT_TYPE_VALUE:
                        kv = DEFAULT_TYPE_VALUE[v]()
                    else:
                        kv = None

            # auto transfer str into ObjectId if possible
            if v is ObjectId and isinstance(kv, str):
                kv = ObjectId(kv)
            test.debug('value is: %s' % kv)
            cd[k] = kv
        return cd

    builtDict = recurse_struct(struct, '')

    if len(default.keys()) > 0:
        raise KeyError('Assignments of default value `%s` failed' % default)

    return builtDict


def index_dict(doc, dot_key):
    """
    Index out values in a dict by dot_key,
    if doc_key represent multi values,
    it will return tuple in order to distinct from list

    Note that it will raise KeyError if cant index out

    Return:
        1. tuple of values
        2. non-tuple value
    """
    def recurse_dict(d, klist):
        try:
            k = klist.pop(0)
        except:
            return d

        if '*' == k:
            if isinstance(d, list):
                d = tuple(d)
            elif isinstance(d, tuple):
                nl = []
                for i in d:
                    if isinstance(i, list):
                        nl.extend(i)
                    else:
                        nl.append(i)
                d = tuple(nl)
        elif isinstance(d, tuple):
            nl = []
            for i in d:
                if isinstance(i, list):
                    for j in i:
                        nl.append(j[k])
                else:
                    nl.append(i[k])
            d = tuple(nl)
        else:
            d = d[k]
        return recurse_dict(d, klist)

    spKeys = dot_key.split('.')
    spKeys.pop(0)

    return recurse_dict(doc, spKeys)


def dict_mapping(o):
    def recurse_doc(mapping, d, pk):
        if isinstance(d, dict):
            for k, v in d.iteritems():
                ck = pk + '.' + k
                recurse_doc(mapping, v, ck)
        elif isinstance(d, list):
            for loop, i in enumerate(d):
                ck = pk + '.' + str(loop)
                recurse_doc(mapping, i, ck)
        else:
            mapping[pk] = d
        return mapping

    return recurse_doc({}, o, '$')


def dict_hash(o):
    mapping = dict_mapping(o)
    keys = mapping.keys()
    keys.sort()
    string = ''
    for i in keys:
        string += i + repr(mapping[i]) + '\n'
    return md5(string).hexdigest()


class DotDict(dict):
    """
    get value in dot retrieve style
    """
    def __init__(self, raw=None):
        super(DotDict, self).__init__()
        if raw is not None:
            assert isinstance(raw, dict), 'DotDict initializing argument is not a dict'
            for k, v in raw.iteritems():
                self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return '<DotDict %s >' % self.normalize()

    def normalize(self):
        d = {}
        for k in self.keys():
            d[k] = self[k]
        return d
