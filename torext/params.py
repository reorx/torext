#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import copy
import functools
import tornado.escape
from torext.errors import ValidationError, ParamsInvalidError, JSONDecodeError


# don't know where to find the <type '_sre.SRE_Pattern'>
_pattern_class = re.compile('').__class__


class Field(object):
    """
    Basic conditions:
      * length range
      * regex pattern
      # * transferable type (int, float, eg.)

    >>> v = BaseField('should not contain int')
    >>> s = 'oh123'
    >>> v.validate(s)
    ValidationError: should not contain int
    """
    name = None

    def __init__(self, description=None, key=None, required=False, length=None, choices=None):
        self.description = description  # default message
        self.required = required  # used with ParamSet
        self.choices = choices
        self.key = key

        self.min_length = None
        assert length is None or isinstance(length, (int, tuple))
        if isinstance(length, int):
            assert length > 0
        if isinstance(length, tuple):
            assert len(length) == 2 and length[0] > 0
            if length[1] == 0:
                self.min_length = length[0]
            else:
                assert length[1] > length[0]
        self.length = length

    #@property
    #def name(self):
        #raise NotImplementedError

    def raise_exc(self, error_message=None):
        raise ValidationError(self.description, error_message)

    def validate(self, value):
        if not value:
            raise ValidationError('value should be empty')

        if self.choices and not value in self.choices:
            raise ValidationError('value "%s" is not one of %s' % (value, self.choices))

        if not self.length:
            return value
        length = self.length
        value_len = len(value)

        if isinstance(length, int):
            if value_len != length:
                self.raise_exc('Length of value should be %s, but %s' % (length, value_len))
        else:
            if self.min_length:
                if value_len < self.min_length:
                    self.raise_exc('Length of value should be larger than %s' % self.min_length)
            else:
                min, max = length
                if value_len < min or value_len > max:
                    self.raise_exc('Length should be >= %s and <= %s, but %s' % (min, max, value_len))

        return value

    def __get__(self, owner, cls):
        return owner.data.get(self.key, None)

    def spawn(self, **kwargs):
        new = copy.copy(self)
        new.__dict__.update(kwargs)
        #for k, v in kwargs.iteritems():
            #setattr(new, k, v)
        return new


class RegexField(Field):
    def __init__(self, *args, **kwgs):
        # assume pattern is a raw string like r'\n'
        if 'pattern' in kwgs:
            pattern = kwgs.pop('pattern')
            self.regex = re.compile(pattern)
        assert hasattr(self, 'regex'),\
            'regex should be set if no keyword argument pattern passed'
        assert isinstance(self.regex, _pattern_class),\
            'regex should be a compiled pattern'

        super(RegexField, self).__init__(*args, **kwgs)

    def validate(self, value):
        value = super(RegexField, self).validate(value)

        #print 'value', value
        if not self.regex.search(value):
            self.raise_exc('regex pattern (%s, %s) is not match with value "%s"' %
                           (self.regex.pattern, self.regex.flags, value))
        return value


class WordField(RegexField):
    regex = re.compile(r'^[\w]+$')


# take from Django
EMAIL_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain


class EmailField(RegexField):
    regex = EMAIL_REGEX


URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class URLField(RegexField):
    regex = URL_REGEX


class IntegerField(Field):
    def __init__(self, *args, **kwargs):
        min = kwargs.pop('min', None)
        max = kwargs.pop('max', None)
        if min is not None:
            assert isinstance(min, int)
        if max is not None:
            assert isinstance(max, int)
        if min is not None and max is not None:
            assert min <= max

        self.min = min
        self.max = max

        super(IntegerField, self).__init__(*args, **kwargs)

    def validate(self, value):
        value = super(IntegerField, self).validate(value)

        try:
            value = int(value)
        except (ValueError, TypeError):
            self.raise_exc('could not convert value "%s" into int type' % value)

        if self.min:
            if value < self.min:
                self.raise_exc('value is too small, min %s' % self.min)
        if self.max:
            if value > self.max:
                self.raise_exc('vaule is too big, max %s' % self.max)

        return value


# TODO
class FloatField(Field):
    pass


# TODO
class DataField(Field):
    pass


class ListField(Field):
    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError('Not a list')
        return value


class ParamSetMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = {}
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                v.name = k
                if not v.key:
                    v.key = k
                fields[k] = v
        attrs['_fields'] = fields
        return type.__new__(cls, name, bases, attrs)


# TODO user-define check function
class ParamSet(object):
    """
    item in `errors` could be:
        tuple: (key, ValidationError)
        exception: ValidationError
    """
    __metaclass__ = ParamSetMeta
    __datatype__ = 'form'  # or 'json'

    def __init__(self, **kwargs):
        self.raw_data = kwargs
        self.data = {}
        self.errors = []

        self.validate()

    def validate(self):
        for name, field in self.__class__._fields.iteritems():
            key = field.key
            if key in self.raw_data:
                raw_value = self.raw_data[key]
                if not isinstance(field, ListField) and\
                        isinstance(raw_value, list):
                    # tornado request.arguments hack, value may be a list,
                    # only use the first one
                    # NOTE do not change request.arguments
                    raw_value = raw_value[0]
                    self.raw_data[key] = raw_value

                try:
                    value = field.validate(raw_value)
                    func_name = 'validate_' + name
                    if hasattr(self, func_name):
                        value = getattr(self, func_name)(value)
                        assert value is not None, 'Forget to return value after validation?'
                except ValidationError, e:
                    self.errors.append((key, e))
                else:
                    self.data[key] = value
            else:
                if field.required:
                    try:
                        field.raise_exc('%s is required' % key)
                    except ValidationError, e:
                        self.errors.append((key, e))

        for attr_name in dir(self):
            if attr_name.startswith('validate_') and\
                    attr_name[len('validate_'):] not in self._fields:
                try:
                    getattr(self, attr_name)()
                except ValidationError, e:
                    self.errors.append(e)

    def has(self, name):
        return name in self.data

    def __str__(self):
        return '<%s: %s; errors=%s>' % (self.__class__.__name__,
                                        ','.join(['%s=%s' % (str(k), str(v)) for k, v in self.data.iteritems()]),
                                        self.errors)

    @classmethod
    def validation_required(cls, method):
        @functools.wraps(method)
        def wrapper(hdr, *args, **kwgs):
            if 'json' == cls.__datatype__:
                try:
                    arguments = tornado.escape.json_decode(hdr.request.body)
                except Exception, e:
                    raise JSONDecodeError(str(e))
            else:
                arguments = hdr.request.arguments
            params = cls(**arguments)
            if params.errors:
                raise ParamsInvalidError(params.errors)
            hdr.params = params
            return method(hdr, *args, **kwgs)
        return wrapper


def define_params(kwargs):
    param_class = type('AutoCreatedParams', (ParamSet, ), kwargs)
    return param_class.validation_required
