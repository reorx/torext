#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Validator is helpful to validate strings


import re
from torext.errors import ValidationError


# don't know where to find the <type '_sre.SRE_Pattern'>
_pattern_class = re.compile('').__class__


class BaseValidator(object):
    """
    Basic conditions:
      * length range
      * regex pattern
      # * transferable type (int, float, eg.)

    >>> v = BaseValidator('should not contain int')
    >>> s = 'oh123'
    >>> v.check(s)
    ValidationError: should not contain int
    """
    def __init__(self, min=None, max=None, message=None):
        self.min = min
        self.max = max
        self.message = message  # default message

    def get_message(self):
        return self.message or 'missing validation message'

    def raise_exc(self, spec_message=None):
        message = self.get_message()
        if spec_message:
            message = spec_message
        raise ValidationError('%s, got: %s' %\
                (message, self.value))

    def __call__(self, s):
        self.value = s
        if self.min:
            if not len(s) >= self.min:
                self.raise_exc('length is too short, min %s' % self.min)
        if self.max:
            if not len(s) <= self.max:
                self.raise_exc('length is too long, max %s' % self.max)

        return self.value


class RegexValidator(BaseValidator):

    def __init__(self, *args, **kwgs):
        if 'regex' in kwgs:
            self.regex = kwgs.pop('regex')
        assert hasattr(self, 'regex') and isinstance(self.regex, _pattern_class),\
                'regex should be set'

        super(RegexValidator, self).__init__(*args, **kwgs)

    def get_message(self):
        if self.message:
            return self.message
        else:
            message = 'not fit regex(%s, %s)' %\
                        (self.regex.pattern, self.regex.flags)
            return message

    def get_pattern(self):
        raise NotImplementedError('get_pattern is expected to be rewritten')

    def __call__(self, s):
        super(RegexValidator, self).__call__(s)

        if not self.regex.search(s):
            self.raise_exc()

        return self.value


class WordsValidator(RegexValidator):
    regex = re.compile(r'^[\w]+$')


class EmailValidator(RegexValidator):
    regex = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')


class URLValidator(RegexValidator):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class IntstringValidator(BaseValidator):
    def __call__(self, s):
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
