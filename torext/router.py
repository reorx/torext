import logging
from tornado.options import options

class SubService(object):
    def __init__(self, svc_label):
        self.import_path = options.package + '.' + svc_label
        self.handlers = []

        try:
            logging.info('import %s' % self.import_path)
            module = __import__(self.import_path, fromlist=[options.package])
            print module
            self.handlers = getattr(module, 'handlers')
        except ImportError, e:
            logging.error(str(e))

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
        handlers = []
        for path, label in self.raw:
            if isinstance(label, SubService):
                for subPath, handler in label.handlers:
                    pattern = r'%s%s' % (path, subPath)
                    handlers.append(
                            (format_pattern(pattern), handler)
                    )
            else:
                pattern = r'%s' % path
                handlers.append(
                        (format_pattern(pattern), label)
                )
        return handlers
