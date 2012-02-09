#!/usr/bin/python
# -*- coding: utf-8 -*-


class OneInstanceImp(object):
    """Our global program options, an dictionary with object-like access.

    Usage::
        >>> class SpecObject(OneInstanceImp):
        >>>     pass

        >>> ins = SpecObject.instance()
    """
    @classmethod
    def instance(cls, *args, **kwgs):
        """Will be the only instance"""
        if not hasattr(cls, "_instance"):
            cls._instance = cls(*args, **kwgs)
        return cls._instance


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
