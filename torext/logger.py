#!/usr/bin/python
# -*- coding: utf-8 -*-
#

import logging
import traceback
import time
import sys


# borrow from tornado.options._LogFormatter.__init__
def _color(lvl, s):
    try:
        import curses
    except ImportError:
        curses = None
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except:
            pass
    if not color:
        return s
    # The curses module has some str/bytes confusion in
    # python3.  Until version 3.2.3, most methods return
    # bytes, but only accept strings.  In addition, we want to
    # output these strings with the logging module, which
    # works with unicode strings.  The explicit calls to
    # unicode() below are harmless in python2 but will do the
    # right conversion in python 3.
    fg_color = (curses.tigetstr("setaf") or
                curses.tigetstr("setf") or "")
    if (3, 0) < sys.version_info < (3, 2, 3):
        fg_color = unicode(fg_color, "ascii")
    colors_map = {
        logging.DEBUG: unicode(curses.tparm(fg_color, 4),  # Blue
                               "ascii"),
        logging.INFO: unicode(curses.tparm(fg_color, 2),  # Green
                              "ascii"),
        logging.WARNING: unicode(curses.tparm(fg_color, 3),  # Yellow
                                 "ascii"),
        logging.ERROR: unicode(curses.tparm(fg_color, 1),  # Red
                               "ascii"),
    }
    _normal = unicode(curses.tigetstr("sgr0"), "ascii")

    return colors_map.get(lvl, _normal) + s + _normal

################
#  formatters  #
################


class BaseFormatter(logging.Formatter):
    def __init__(self, *args, **kwgs):
        color = False
        if 'color' in kwgs:
            color = kwgs.pop('color')
        datefmt = '%Y-%m-%d %H:%M:%S'
        if 'datefmt' in kwgs:
            datefmt = kwgs['datefmt']
        logging.Formatter.__init__(self, *args, **kwgs)
        self.color = color
        self.datefmt = datefmt

    def format(self, record):
        try:
            message = record.getMessage()
        except Exception, e:
            message = 'Could not get message, error: %s' % e
        # record.asctime = time.strftime(
        #     , self.converter(record.created))
        # record.asctime =
        levelname = record.levelname
        if record.levelname == 'DEBUG':
            levelname = 'DBG'
        elif record.levelname == 'WARNING':
            levelname = 'WARN'
        elif record.levelname == 'ERROR':
            levelname = 'ERRO'
        if self.color:
            levelname = _color(record.levelno, levelname)
        record_dict = {
            'levelname': levelname,
            'asctime': self.formatTime(record, self.datefmt),
            'module_with_lineno': '%s-%s' %\
                (record.module, record.lineno),
            'message': message
        }
        log = '. {levelname:<4} {asctime} {module_with_lineno:<10}. {message}'.format(**record_dict)
        if record.exc_info:
            log += '\n' + traceback.format_exc()
            # log += err_info
        if '\n' in log and not log.endswith('\n'):
            suffix = '\n'
        else:
            suffix = ''
        return log.replace('\n', '\n  ') + suffix

#############
#  loggers  #
#############
# 1. test - propagate 0
# 2. system - propagate 1 - for seperately output system level logs

testLogger = logging.getLogger('plain')
testLogger.propagate = 0
testLogger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(BaseFormatter(color=True))
    root_logger.addHandler(streamHandler)

    root_logger.info('hello')
    root_logger.warning('\nholy a shit')
    try:
        tuple()[0]
    except Exception, e:
        root_logger.error(e, exc_info=True)

    # this logger's log will be handled only once, due to the bool False value
    # of testLogger's attribute `propagate`
    testLogger.addHandler(logging.StreamHandler())
    testLogger.info('my name is testLogger')

    # this logger's log will be handled twice, one by its self, with uncustomized StreamHandler instance,
    # the other by rootLogger, which is the parent of otherLogger, see quote below::
    #
    # http://docs.python.org/howto/logging.html#loggers
    #
    #     " Child loggers propagate messages up to the handlers associated
    #     with their ancestor loggers. Because of this, it is unnecessary to
    #     define and configure handlers for all the loggers an application
    #     uses. It is sufficient to configure handlers for a top-level
    #     logger and create child loggers as needed. (You can, however, turn
    #     off propagation by setting the propagate attribute of a logger to
    #     False.) "
    otherLogger = logging.getLogger('other')
    otherLogger.addHandler(logging.StreamHandler())
    otherLogger.info('here is otherLogger')

    # and this logger, its log will ofcoursely be handled three times
    otherBabyLogger = logging.getLogger('other.baby')
    otherBabyLogger.addHandler(logging.StreamHandler())
    otherBabyLogger.info('here is otherBabyLogger')
