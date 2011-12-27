#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import threading


class ThreadWorker(threading.Thread):
    def __init__(self, task_fn):
        self.task_fn = task_fn
        super(ThreadWorker, self).__init__()

    def run(self, *args, **kwgs):
        logging.info('worker:: start..')
        self.task_fn(*args, **kwgs)
        logging.info('worker:: done..')

def do_task(task_fn, *args, **kwgs):
    logging.info('task:: init %s' % str(task_fn))
    ThreadWorker(task_fn).start(*args, **kwgs)
