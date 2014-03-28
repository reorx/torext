#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import inspect


class Command(object):
    def __init__(self, func, options=None):
        self.func = func
        parser = argparse.ArgumentParser(
            description='Calling function %s in manager script' % func.__name__)
        if isinstance(options, tuple):
            parser.add_argument()
        pass


class Manager(object):
    def __init__(self, app):
        self.commands = {}
        pass

    def run(self):
        pass

    # Flask-Script like decorators

    def command(self, func=None, options=None):
        """
        @manager.command
        def foo():
            pass

        @manager.command(options=('-n', help='xx'))
        def foo(args):
            pass

        @manager.command(options=[
            ('-a'),
            ('-b'),
            ('-c')
        ])
        def foo(args):
            pass
        """
        if func:
            assert inspect.isfunction(func)
            self.add_command(func)
            return func

        if options:
            def wrapper(_func):
                self.add_command(_func, options)
                return _func
            return wrapper

        raise Exception('You should call add_command\
                        with both `func` and `options` argument')

    def add_command(self, func, options=None):
        self.commands[func.__name__] = Command(func, options)


# Fabric like utilities

def confirm():
    pass
