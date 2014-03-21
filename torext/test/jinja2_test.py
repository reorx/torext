#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import jinja2
except ImportError:
    print 'jinja2 is not installed, skip testing'
    from nose.plugins.skip import SkipTest
    raise SkipTest


def test_jinja2_render():
    from torext import settings
    from torext.handlers.base import jinja2_render

    # Fake settings
    settings['PROJECT'] = 'torext'
    settings['TEMPLATE_PATH'] = 'test/jinja2'

    context = {
        'name': 'Jinja2'
    }
    rendered = jinja2_render('template.html', **context)

    assert rendered == jinja2_render('rendered.html')
