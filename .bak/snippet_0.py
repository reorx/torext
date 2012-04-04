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


##################################################
# borrow from django.utils.functional.LazyObject #
##################################################

class DummyObject(object):
    """
    A wrapper for reading attributes from another object instantly (no delay)
    """
    def __init__(self, entity):
        # TODO 'if self._entity is None, then..' this way can be improved
        self._entity = self._init_entity(entity)
        if self._entity is None:
            raise ValueError('_entity of DummyObject should not be None')

    def __getattr__(self, name):
        return getattr(self._entity, name)

    def __setattr__(self, name, value):
        if name == "_entity":
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__["_entity"] = value
        else:
            setattr(self._entity, name, value)

    def __delattr__(self, name):
        if name == "_entity":
            raise TypeError("can't delete _entity.")
        delattr(self._entity, name)

    def _init_entity(self):
        """
        Must be implemented by subclasses to initialise the wrapped object.

        return the entity to be used
        """
        raise NotImplementedError

    # introspection support: (is that useful ?)
    # __members__ = property(lambda self: self.__dir__())

    def __dir__(self):
        return  dir(self._entity)



