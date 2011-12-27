#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
import _ast
import logging

checker = __import__('pyflakes.checker').checker

LOG_FILE_NAME_SUFFIX = '.syntax.log'

def check(codeString, filename):
    """
    Check the Python source given by C{codeString} for flakes.

    @param codeString: The Python source to check.
    @type codeString: C{str}

    @param filename: The name of the file the source came from, used to report
        errors.
    @type filename: C{str}

    @return: The number of warnings emitted.
    @rtype: C{int}
    """
    # First, compile into an AST and handle syntax errors.
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError, value:
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            logging.error("%s: problem decoding source" % (filename, ))
        else:
            line = text.splitlines()[-1]

            if offset is not None:
                offset = offset - (len(text) - len(line))

            logging.error('%s:%d: %s' % (filename, lineno, msg))
            logging.error(line)

            if offset is not None:
                logging.error(" " * offset, "^")

        return 1
    else:
        # Okay, it's syntactically valid.  Now check it.
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for warning in w.messages:
            logging.warning(warning)
        return len(w.messages)


def checkPath(filename):
    """
    Check the given path, printing out any warnings detected.

    @return: the number of warnings printed
    """
    try:
        return check(file(filename, 'U').read() + '\n', filename)
    except IOError, msg:
        print >> sys.stderr, "%s: %s" % (filename, msg.args[1])
        return 1


def main():
    # TODO parameter parse
    root = sys.argv[1]

    if root.endswith('/'):
        root = root[:-1]
    if os.path.isdir(root):
        log_file_name = root + '_dir' + LOG_FILE_NAME_SUFFIX
    else:
        log_file_name = root + LOG_FILE_NAME_SUFFIX
    if os.path.exists(log_file_name):
        os.remove(log_file_name)

    # TODO prettified logger class
    logging.basicConfig(filename=log_file_name, level=logging.DEBUG)

    logging.info('start checking')
    warnings = 0
    for dirpath, dirnames, fnames in os.walk(root):
        for i in fnames:
            if i.endswith('.py'):
                # TODO ignore warning by certain format comment
                warnings += checkPath(os.path.join(dirpath, i))
    logging.info('warnings number: %s' % warnings)


if __name__ == '__main__':
    main()
