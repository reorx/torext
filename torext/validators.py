#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
from torext.errors import ValidationError, ParametersInvalid


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
    def __init__(self, message=None, required=False, min=None, max=None):
        self.min = min
        self.max = max
        self.message = message  # default message
        self.required = required

    #def __get__(self, instance, owner):
        #return instance._data[self._attr_name]

    #def __set__(self, instance, value):
        #raise Exception('Params is read only, set or delete is not allowed')

    #def __delete__(self, instance):
        #raise Exception('Params is read only, set or delete is not allowed')

    def get_message(self):
        return self.message or 'missing validation message'

    def raise_exc(self, spec_message=None):
        message = self.get_message()
        if spec_message:
            message = spec_message
        raise ValidationError('%s, got: %s' %
                              (message, self.value))

    def validate(self, s):
        self.value = s
        if self.min:
            if not len(s) >= self.min:
                self.raise_exc('length is too short, min %s' % self.min)
        if self.max:
            if not len(s) <= self.max:
                self.raise_exc('length is too long, max %s' % self.max)

        return self.value


class RegexField(Field):
    def __init__(self, *args, **kwgs):
        # consider pattern as a raw string like r'\n'
        if 'pattern' in kwgs:
            pattern = kwgs.pop('pattern')
            self.regex = re.compile(pattern)
        assert hasattr(self, 'regex') and\
            isinstance(self.regex, _pattern_class), 'regex should be set'

        super(RegexField, self).__init__(*args, **kwgs)

    def get_message(self):
        if self.message:
            return self.message
        else:
            message = 'not fit regex(%s, %s)' %\
                      (self.regex.pattern, self.regex.flags)
            return message

    def get_pattern(self):
        raise NotImplementedError('get_pattern is expected to be rewritten')

    def validate(self, s):
        super(RegexField, self).validate(s)

        if not self.regex.search(s):
            self.raise_exc()

        return self.value


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


class IntstringField(Field):
    def validate(self, s):
        try:
            s = int(s)
        except (ValueError, TypeError):
            self.value = s  # to ensure error raising's success
            self.raise_exc('could not convert into int type')

        self.value = s

        if self.min:
            if not s >= self.min:
                self.raise_exc('value is too small, min %s' % self.min)
        if self.max:
            if not s <= self.max:
                self.raise_exc('vaule is too big, max %s' % self.max)

        return self.value


class DataField(Field):
    pass


class ParamsMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = {}
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                if k.startswith('_'):
                    raise Exception("Params dont support field name starts with '_'")
                fields[k] = v
        attrs['_fields'] = fields
        return type.__new__(cls, name, bases, attrs)


class Params(object):
    __metaclass__ = ParamsMeta

    def __init__(self, **kwgs):
        self._data = kwgs
        self._errors = []
        self.is_valid = False

        self.validate()

    def validate(self):
        for key, field in self.__class__._fields.iteritems():
            if key in self._data:
                value = self._data[key]
                try:
                    field.validate(value)
                except ValidationError, e:
                    self._errors.append(e.__str__())
            else:
                if field.required:
                    self._errors.append('%s is required' % key)
        else:
            self.is_valid = True

    def __getattribute__(self, key):
        if not key.startswith('_'):
            if key in self.__class__._fields:
                if key in self._data:
                    return self._data[key]
                else:
                    raise Exception('%s is not in Params' % key)
        return super(Params, self).__getattribute__(key)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            if key in self.__class__._fields:
                raise Exception('Params dont allow attribute change on fields')
        super(Params, self).__setattr__(key, value)

    def __delattr__(self, key):
        if not key.startswith('_'):
            if key in self.__class__._fields:
                raise Exception('Params dont allow attribute change on fields')
        super(Params, self).__delattr__(key)


if __name__ == '__main__':

    class AParams(Params):
        title = WordField()
        body = WordField(required=True)

    data = {
        'title': 'asdf'
    }
    ap = AParams(**data)
    print ap.title
    print ap.body
    print ap.__class__.title
