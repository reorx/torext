#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.script import Manager

manager = Manager()


@manager.command
def create_database(name, number=1, force_clear=False):
    """Command to create a database
    """
    print 'Got:'
    print 'name', name, type(name)
    print 'number', number, type(number)
    print 'force_clear', force_clear, type(force_clear)


@manager.command
def run(**kwargs):
    """Command to run server, pass `--PORT 9000`, `--TEMPLATE_PATH templates`
    as arguments to affect on global settings object.
    """
    from sampleproject.app import app

    app.update_settings(**kwargs)
    app.run()


@manager.command
def test_env():
    import tornado
    print tornado


if '__main__' == __name__:
    manager.run()
