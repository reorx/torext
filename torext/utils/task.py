#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import threading


class ThreadWorker(threading.Thread):
    def __init__(self, task_fn):
        self.task_fn = task_fn
        super(ThreadWorker, self).__init__()

    def run(self, *args, **kwgs):
        logging.debug('worker:: start..')
        self.task_fn(*args, **kwgs)
        logging.debug('worker:: done..')


def do_task(task_fn, *args, **kwgs):
    logging.debug('task:: init %s' % repr(task_fn))
    ThreadWorker(task_fn).start(*args, **kwgs)
