#!/usr/bin/python
# -*- coding: utf-8 -*-


def pprint(o):
    import pprint as PPrint
    pprinter = PPrint.PrettyPrinter(indent=4)
    pprinter.pprint(o)




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
