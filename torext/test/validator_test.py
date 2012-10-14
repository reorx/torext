#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.testing import _TestCase

import re
from torext.validators import RegexValidator, WordsValidator, EmailValidator, URLValidator, IntstringValidator
from torext.errors import ValidationError


class ValidatorTest(_TestCase):
    def test_regex_0(self):
        v = RegexValidator(regex=re.compile(r'^\w+$'))
        v('hello')
        self.assertRaises(ValidationError, v, 'hi**io')

    def test_regex_1(self):
        v = RegexValidator(regex=re.compile(r'^[\w]+$'))
        v('hasslash')
        self.assertRaises(ValidationError, v, 'hq)ie')

    def test_regex_2(self):
        v = RegexValidator(regex=re.compile(r'\w+'))
        v('wooo')
        v('w*o^oo')

    def test_words(self):
        v = WordsValidator()
        v('yes')
        self.assertRaises(ValidationError, v, 'n&&o')

    def test_words_with_length(self):
        v = WordsValidator(2, 5)
        self.log.quiet('%s, %s' % (v.min, v.max))
        v('xx')
        v('xxooo')
        self.assertRaises(ValidationError, v, 'x')
        self.assertRaises(ValidationError, v, 'xxxooo')

    def test_email(self):
        v = EmailValidator()
        v('hello@wo.co')
        self.assertRaises(ValidationError, v, '*x@cc.sssss')

    def test_url(self):
        v = URLValidator()
        v('http://healksjdf.ssd')
        self.assertRaises(ValidationError, v, 'yuefm://wei.xx')
        self.assertRaises(ValidationError, v, 'http://wei.xax..')

    def test_intstring(self):
        v = IntstringValidator()
        v('123')
        self.assertRaises(ValidationError, v, '1o')

    def test_intstring_with_length(self):
        v = IntstringValidator(10, 100)
        v('23')
        self.assertRaises(ValidationError, v, '1')
        self.assertRaises(ValidationError, v, '101')
