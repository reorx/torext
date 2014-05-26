#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from torext.utils import split_kwargs


try:
    from nose.plugins.logcapture import MyMemoryHandler
except ImportError:
    MyMemoryHandler = None


root_logger = logging.getLogger()


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
        'grey': unicode(curses.tparm(fg_color, 0),  # Grey
                        "ascii"),
    }
    _normal = unicode(curses.tigetstr("sgr0"), "ascii")

    return colors_map.get(lvl, _normal) + s + _normal


FIXED_LEVELNAMES = {
    'DEBUG': 'DEBG',
    'WARNING': 'WARN',
    'ERROR': 'ERRO'
}


class BaseFormatter(logging.Formatter):
    def __init__(self,
                 prefixfmt='[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)s] ',
                 contentfmt='%(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S',
                 color=False,
                 tab=u'  '):
        """
        a log is constituted by two part: prefix + content

        prefix is determined by `prefixfmt`, whose color depends on logging level

        content is what passed to the log method, %(message)s by default
        """
        # as origin __init__ function is very simple
        # (just store two attributes on self: _fmt & datefmt), execute it firstly
        logging.Formatter.__init__(self, datefmt=datefmt)

        self.prefixfmt = prefixfmt
        self.contentfmt = contentfmt
        self.color = color
        self.tab = tab

    def _format_record(self, record):
        record.message = record.getMessage()
        record.fixed_levelname = FIXED_LEVELNAMES.get(record.levelname, record.levelname)

        allfmt = self.contentfmt + self.prefixfmt
        if 'asctime' in allfmt:
            record.asctime = self.formatTime(record, self.datefmt)
        if 'secs' in allfmt:
            record.secs = record.msecs / 1000

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

    def format(self, record):
        """
        return log in unicode
        """
        self._format_record(record)

        prefix = self.prefixfmt % record.__dict__
        if not isinstance(prefix, unicode):
            prefix = prefix.decode('utf8', 'replace')
        if self.color:
            prefix = _color(record.levelno, prefix)

        # print 'prefix', type(prefix), prefix

        # prefix is unicode, so the result of record format must also be unicode
        content = self.contentfmt % record.__dict__
        if not isinstance(content, unicode):
            # If the content is not encoded in utf8, gibberish will be showed
            # instead of raising exception
            content = content.decode('utf8', 'replace')

        # print 'content', type(content), content

        log = prefix + content

        if record.exc_text:
            if log[-1:] != u'\n':
                log += u'\n'
            log += record.exc_text.decode('utf8', 'replace')

        log = log.replace(u'\n', u'\n' + self.tab)

        return log


class BaseStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwgs):
        _kwgs = split_kwargs(
            ('prefixfmt', 'contentfmt', 'datefmt', 'color'), kwgs)

        super(BaseStreamHandler, self).__init__(*args, **kwgs)

        self.setFormatter(BaseFormatter(**_kwgs))


HANDLER_TYPES = {
    'stream': BaseStreamHandler,
}


def set_logger(name,
               level='INFO',
               propagate=1,
               color=True,
               prefixfmt=None,
               contentfmt=None,
               datefmt=None):
    """
    This function will clear the previous handlers and set only one handler,
    which will only be StreamHandler for the logger.

    This function is designed to be able to called multiple times in a context.
    """
    # NOTE if the logger has no handlers, it will be added a handler automatically when it is used.
    # logging.getLogger(name).handlers = []

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    logger.propagate = propagate

    handler = None
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler):
            # use existing instead of clean and create
            handler = h
            break
    if not handler:
        handler = logging.StreamHandler()
        logger.addHandler(handler)

    formatter_kwgs = {}
    for i in ('color', 'prefixfmt', 'contentfmt', 'datefmt'):
        if locals()[i] is not None:
            formatter_kwgs[i] = locals()[i]
    handler.setFormatter(BaseFormatter(**formatter_kwgs))


def set_nose_formatter(logging_options):
    if not MyMemoryHandler:
        return

    formatter_kwgs = {}
    for i in ('color', 'prefixfmt', 'contentfmt', 'datefmt'):
        v = logging_options.get(i)
        if v:
            formatter_kwgs[i] = v
    formatter = BaseFormatter(**formatter_kwgs)

    nose_handler = None
    for h in root_logger.handlers:
        if isinstance(h, MyMemoryHandler):
            h.setFormatter(formatter)
            nose_handler = h
            break

    if nose_handler:
        root_logger.handlers = [nose_handler, ]


#############
#  loggers  #
#############
# 1. test - propagate 0
# 2. system - propagate 1 - for seperately output system level logs

#test_logger = logging.getLogger('test')
#test_logger.propagate = 0
#test_logger.setLevel(logging.INFO)
#test_logger.handlers = []


if __name__ == '__main__':
    def test_all():
        root_logger = logging.getLogger()
        # root_logger.setLevel(logging.INFO)
        # streamHandler = logging.StreamHandler()
        # streamHandler.setFormatter(BaseFormatter(color=True))
        # root_logger.addHandler(streamHandler)
        set_logger('', level=logging.DEBUG, color=True)

        root_logger.debug('bug..')
        root_logger.info('hello')
        root_logger.warning('\nholy a shit')
        try:
            tuple()[0]
        except Exception, e:
            root_logger.error(e, exc_info=True)

        # this logger's log will be handled only once, due to the bool False value
        # of testLogger's attribute `propagate`
        # testLogger.addHandler(logging.StreamHandler())
        # testLogger.info('my name is testLogger')

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
        fmter = logging.Formatter(fmt='%(message)s %(msecs)s')
        hdr = logging.StreamHandler()
        hdr.setFormatter(fmter)
        otherLogger.addHandler(hdr)
        otherLogger.info('here is otherLogger')

        # and this logger, its log will ofcoursely be handled three times
        otherBabyLogger = logging.getLogger('other.baby')
        otherBabyLogger.addHandler(hdr)
        otherBabyLogger.info('here is otherBabyLogger')

    test_all()
