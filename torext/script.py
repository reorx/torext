#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import inspect
import functools
import time
from .errors import CommandArgumentError


class Command(object):
    allow_types = (int, float, str, str, bool)

    def __init__(self, func, profile=False):
        self.func = func
        self.profile_flag = profile

        spec = inspect.getargspec(func)

        argnames = (spec.args or [])[:]
        defaults = list(spec.defaults or [])

        self.parameters = argnames[:len(argnames) - len(defaults)]
        self.keyword_parameters = dict(list(zip(argnames[- len(defaults):], defaults)))

        # Check defined keyword parameters
        for k, v in self.keyword_parameters.items():
            self._get_value_type(v)

        self.has_varargs = bool(spec.varargs)
        self.has_kwargs = bool(spec.keywords)

        if func.__doc__:
            doc = func.__doc__
            if '\n' in doc:
                doc = ' '.join(i.strip() for i in doc.split('\n'))
        else:
            doc = "Command '%s' in manage script" % func.__name__
        self.doc = doc

    def parse_args(self, all_args=None):
        if all_args is not None:
            all_args = all_args[:]
        else:
            all_args = sys.argv[2:]

        _kw_pos = []
        for loop, i in enumerate(all_args):
            if i.startswith('--'):
                _kw_pos.append(loop)

        if _kw_pos:
            # Check positions
            all_args_len = len(all_args)
            _fixed_kw_pos = _kw_pos + [all_args_len]
            for loop, i in enumerate(_fixed_kw_pos):
                if i == all_args_len:
                    continue
                if _fixed_kw_pos[loop + 1] - i != 2:
                    raise CommandArgumentError(
                        'Invalid arguments: %s should have one and only one value' % all_args[i])

            # Get args and keyword_args
            args = all_args[:_kw_pos[0]]
            #keyword_args = {all_args[i][2:]: all_args[i + 1] for i in _kw_pos}
            keyword_args = dict((all_args[i][2:], all_args[i + 1]) for i in _kw_pos)
        else:
            args = all_args
            keyword_args = {}

        # Check args
        if len(args) < len(self.parameters):
            raise CommandArgumentError('Arguments too little')
        else:
            if not self.has_varargs and\
               len(args) > len(self.parameters) + len(self.keyword_parameters):
                raise CommandArgumentError('Arguments too much')

        # Check keyword args
        if not self.has_kwargs:
            for i in keyword_args:
                if not i in self.keyword_parameters:
                    raise CommandArgumentError('Unknown keyword parameter %s' % i)

        # Convert keyword args type
        # NOTE As keyword arguments passed as arguments are allwed,
        # and only recognized keyword arguments will be converted,
        # so keyword arguments passed as arguments will not be converted.
        for i in keyword_args:
            if i in self.keyword_parameters:
                default = self.keyword_parameters[i]
                converted = self._convert_to_type(
                    keyword_args[i], self._get_value_type(default))
                keyword_args[i] = converted

        return args, keyword_args

    def _get_value_type(self, value):
        if isinstance(value, self.allow_types):
            typ = type(value)
        elif value is None:
            typ = None
        else:
            raise TypeError('Parameters for command function can only be type of %s' % self.allow_types)
        return typ

    def _convert_to_type(self, source, typ):
        if typ in (int, float, str, str):
            try:
                v = typ(source)
            except ValueError:
                raise CommandArgumentError("'%s' could not be converted to %s"
                                           % (source, typ))
        elif typ == bool:
            if source in ('True', '1'):
                v = True
            elif source in ('False', '0'):
                v = False
            else:
                raise CommandArgumentError("'%s' could not be converted to bool type" % source)
        elif typ is None:
            v = source

        return v

    def execute(self, all_args=()):
        if not all_args:
            return self.func()
        else:
            args, keyword_args = self.parse_args(all_args)
            return self.func(*args, **keyword_args)


class Manager(object):
    def __init__(self, app=None):
        self.app = app
        self._commands = {}
        self._commands_list = []

    def run(self):
        all_args = sys.argv[1:]
        if not all_args or all_args[0] in ('-h', '--help'):
            self.print_usage()
            return

        if all_args[0] not in self._commands:
            self.print_small_help("'{}' is not a command".format(all_args[0]))
            return

        # Execute
        command = self._commands[all_args[0]]
        try:
            stime = time.time()
            command.execute(all_args[1:])
            if command.profile_flag:
                print("spend time: {}".format(float(time.time() - stime)))
        except CommandArgumentError as e:
            print('Command execution failed: {}'.format(e))
            self.print_command_help(command)

    def print_command_help(self, command):
        buf = []
        buf.append("'%s' usage:".format(command.func.__name__))
        buf.append("  Arguments        : {}".format(','.join(command.parameters)))
        buf.append("  Keyword arguments: {}".format(','.join('%s=%s' % (k, v) for k, v in command.keyword_parameters.items())))
        print('\n'.join(buf))

    def print_small_help(self, hint=None):
        s = "Type '%s -h' or '%s --help' for more information"
        if hint:
            print(hint + '\n' + s)
        else:
            print(s)

    def print_usage(self, hint=None):
        """Usage format should be like:
        Lineno | Content
             1 | Script description (__doc__)
             2 | Usage: {script name} [COMMAND] [ARGUMENTS]
             3 | \n
             4 | Commands:
             5 |   cmd1               cmd1 description.
             6 |   cmd2isverylong     cmd2 description, and it is also
             7 |                      long as shit.
             7 |   cmd3               cmd3 description.
        """
        buf = []

        # Description
        if __doc__:
            buf.append(__doc__)

        # Usage
        script_name = sys.argv[0]
        buf.append('Usage: %s [COMMAND] [ARGUMENTS]' % script_name)

        buf.append('')
        buf.append('Commands:')

        # Commands
        indent_size = 2
        tab_size = 4
        doc_width = 50
        grid_len = max(len(i) for i in list(self._commands.keys())) + tab_size

        for name in self._commands_list:
            command = self._commands[name]
            line = ' ' * indent_size + name + ' ' * (grid_len - len(name))
            doc = command.doc
            pieces = [doc[i:i + doc_width] for i in range(0, len(doc), doc_width)]
            line += pieces[0]
            if len(pieces) > 1:
                line += '\n'
                line += '\n'.join(' ' * (grid_len + 2) + i for i in pieces[1:])

            buf.append(line)

        print('\n'.join(buf))

    def prepare(self, setup_func):
        """This decorator wrap a function which setup a environment before
        running a command
        @manager.prepare(setup_func)
        def some_command():
            pass
        """
        assert inspect.isfunction(setup_func)
        argsspec = inspect.getargspec(setup_func)
        if argsspec.args:
            raise ValueError("prepare function shouldn't have any arguments")

        def decorator(command_func):
            @functools.wraps(command_func)
            def wrapper(*args, **kwgs):
                # Run setup_func before command_func
                setup_func()
                return command_func(*args, **kwgs)
            return wrapper
        return decorator

    def command(self, profile=False):
        """This is a Flask-Script like decorator, provide functionality like
        @manager.command
        def foo():
            pass

        @manager.command
        def foo(first_arg, second_arg, first_option=True, second_option=3):
            pass
        """
        def wraped(func):
            assert inspect.isfunction(func)

            self._commands[func.__name__] = Command(func, profile)
            self._commands_list.append(func.__name__)

            return func
        return wraped

    def _init_default_commands(self):
        # TODO
        # init_completion
        pass


# Fabric like utilities

def confirm():
    pass
