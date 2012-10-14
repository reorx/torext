#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# make a project sketch.

import os
import re
import sys
import shutil
import optparse
import torext
from torext.utils import import_module


parser = optparse.OptionParser(usage='Usage: %prog [options] arg1')
parser.add_option('-f', '--flask-style', action='store_true', default=False)


class CommandInputError(Exception):
    def __init__(self, msg):
        self.msg = msg
        print self.__str__() + '\n'
        parser.print_help()
        sys.exit()

    def __str__(self):
        return self.__class__.__name__ + ': %s' % self.msg


def main():
    options, args = parser.parse_args()

    try:
        name = args[0]
    except IndexError:
        raise CommandInputError('one arg is required')
    # If it's not a valid directory/file name.
    if not re.search(r'^[_a-zA-Z]\w*$', name):
        # Provide a smart error message, depending on the error.
        if not re.search(r'^[_a-zA-Z]', name):
            message = 'make sure the name begins with a letter or underscore'
        else:
            message = 'use only numbers, letters and underscores'
        raise CommandInputError(message)

    cwd = os.getcwd()
    torext_path = os.path.dirname(torext.__file__)

    if not options.flask_style:
        # Check that the project_name cannot be imported.
        try:
            import_module(name)
        except ImportError:
            pass
        else:
            raise CommandInputError("%r conflicts with the name of an existing Python module\
                and cannot be used as a project name. Please try another name." % name)

        template_path = os.path.join(torext_path, 'templates/project')
        target_path = os.path.join(cwd, name)
        assert not os.path.exists(target_path), 'You indicate an existing dir, could not be used for sketch'
        shutil.copytree(template_path, target_path)

    else:
        template_path = os.path.join(torext_path, 'templates/flask_style.py')
        target_path = os.path.join(cwd, '%s.py' % name)
        assert not os.path.exists(target_path), 'You indicate an existing file, could not be used for sketch'
        shutil.copyfile(template_path, target_path)


if __name__ == '__main__':
    main()
