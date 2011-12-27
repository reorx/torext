import os
import sys
import pkgutil
import logging

_abspath = lambda x: os.path.abspath(x)
_join = lambda x, y: os.path.join(x, y)
_abs_join = lambda x, y: _abspath(_join(x, y))


def import_underpath_module(path, name):
    """
    arguments::
    :name :: note that name do not contain `.py` at the end
    """
    importer = pkgutil.get_importer(path)
    logging.warning('loading handler module: ' + name)
    return importer.find_module(name).load_module(name)

def autoload_submodules(dirpath):
    """Load submodules by dirpath
    NOTE. ignore packages
    """
    import pkgutil
    importer = pkgutil.get_importer(dirpath)
    return (importer.find_module(name).load_module(name)\
            for name, is_pkg in importer.iter_modules())

#####################################################
#                                                   #
#    some may-be-userful code pieces from django    #
#                                                   #
#####################################################

# Taken from Python 2.7 with permission from/by the original author.

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]
