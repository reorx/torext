#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# syntax checker, walk through the project or just a single file.

import os
import sys
import _ast
import logging
import logging.handlers

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

            logging.error('[{0:4}] {1}'.format(lineno, msg))
            gap = ' ' * 7
            logging.error(gap + line)

            if offset is not None:
                logging.error(gap + ' ' * offset + '^')

        return 1
    else:
        # Okay, it's syntactically valid.  Now check it.
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for warning in w.messages:
            #print dir(warning)
            logging.warning('[{0:4}] {1}'.format(warning.lineno, warning.message % warning.message_args))
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


class SharedLogFormatter(logging.Formatter):
    #def __init__(self):

    def format(self, record):
        """
        debug:
        ----------[dir/]----------

        info:
        [info]

        warning & error:
          [W]
          [E]
        """
        #print 'in Formater'
        l = record.levelname
        try:
            msg = record.getMessage()
        except:
            msg = 'OMG'
        fmted = ''
        if 'DEBUG' == l:
            fmted = '----------[{0:10}]----------'.format(msg)
        elif 'INFO' == l:
            fmted = '- ' + msg
        elif 'WARNING' == l:
            fmted = '  [W]' + msg
        elif 'ERROR' == l:
            fmted = '  [E]' + msg
        return fmted


def main():
    # TODO parameter parse
    from optparse import OptionParser
    parser = OptionParser(usage='Usage: %prog [options] arg1 arg2 ..')
    parser.add_option('-w', '--write-log', action='store_true')
    parser.add_option('-o', '--output-file', default='torext_syntax_checker.log')

    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error('one file or directory should be pointed')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    formatter = SharedLogFormatter()
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    if options.write_log:
        #if os.path.exists(options.output_file):
            #os.remove(options.output_file)
        fi = logging.handlers.RotatingFileHandler(options.output_file, mode='w')
        fi.setFormatter(formatter)
        root_logger.addHandler(fi)

    for pth in args:
        logging.debug(pth)
        warnings = 0
        if os.path.isdir(pth):
            for dirpath, dirnames, fnames in os.walk(pth):
                for i in fnames:
                    if i.endswith('.py'):
                        # TODO ignore warning by certain format comment
                        logging.info(i)
                        warnings += checkPath(os.path.join(dirpath, i))
        else:
            logging.info(pth)
            warnings = checkPath(pth)
        logging.info('warnings number: %s' % warnings)
        logging.info('::end')


if __name__ == '__main__':
    main()
