#!/usr/bin/python
# -*- coding: utf-8 -*-

__all__ = ['Form',
           'BooleanField', 'TextField', 'PasswordField',
           'SelectField', 'DateField', 'TextAreaField',
           'IntegerField', 'ValidationError', 'validators', ]

import re

import tornado.locale
from tornado.escape import to_unicode

from wtforms import Form as wtForm
from wtforms import BooleanField, TextField, PasswordField
from wtforms import SelectField, DateField, TextAreaField
from wtforms import IntegerField
from wtforms import ValidationError
from wtforms import validators

class TornadoArgumentsWrapper(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError

    def getlist(self, key):
        try:
            values = []
            for v in self[key]:
                v = to_unicode(v)
                if isinstance(v, unicode):
                    v = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", v)
                values.append(v)
            return values
        except KeyError:
            raise AttributeError

class TornadoLocaleWrapper(object):
    def __init__(self, code):
        self.locale = tornado.locale.get(code)

    def gettext(self, message):
        return self.locale.translate(message)

    def ngettext(self, message, plural_message, count):
        return self.locale.translate(message, plural_message, count)

class Form(wtForm):
    """
    Add translating ability to wtForm

    Using this Form instead of wtforms.Form

    Example::

        class SigninForm(Form):
            email = EmailField('email')
            password = PasswordField('password')

        class SigninHandler(RequestHandler):
            def get(self):
                form = SigninForm(self.request.arguments)

    """
    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        self._locale_code = kwargs.get('locale_code', 'en_US')
        self.model = kwargs.get('model', None)
        super(Form, self).__init__(formdata, obj, prefix, **kwargs)

    def process(self, formdata=None, obj=None, **kwargs):
        if formdata is not None and not hasattr(formdata, 'getlist'):
            formdata = TornadoArgumentsWrapper(formdata)
        super(Form, self).process(formdata, obj, **kwargs)

    def _get_translations(self):
        if not hasattr(self, '_locale_code'):
            self._locale_code = 'en_US'
        return TornadoLocaleWrapper(self._locale_code)

    def _debug(self):
        print 'form errors: ', self.errors
