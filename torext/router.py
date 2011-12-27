from tornado.options import options

from .utils.importlib import _abspath, _join
from .utils.importlib import import_underpath_module

class SubService(object):
    def __init__(self, svc_label):
        svc_sp = svc_label.split('.')
        self.module_name = svc_sp.pop(-1)
        buf = options.app['root']
        for i in svc_sp:
            buf = _join(buf, i)
        self.module_parent_path = _abspath(buf)

    def get_handlers(self):
        module = import_underpath_module(
                self.module_parent_path, self.module_name)
        return getattr(module, 'handlers', None)

def include(*args):
    return SubService(*args)

class Router(object):
    def __init__(self, raw):
        self.raw = raw

    def get_handlers(self):
        def format_pattern(pt):
            if pt.endswith('/') and len(pt) > 1:
                pt = pt[:-1]
            return pt
        hdrs = []
        for i in self.raw:
            if isinstance(i[1], SubService):
                for j in i[1].get_handlers():
                    pattern = r'%s%s' % (i[0], j[0])
                    hdrs.append(
                            (format_pattern(pattern), j[1])
                    )
            else:
                pattern = r'%s' % i[0]
                hdrs.append(
                        (format_pattern(pattern), i[1])
                )
        return hdrs
