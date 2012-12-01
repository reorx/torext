#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import torext
from torext.app import TorextApp


if __name__ == '__main__':
    import settings
    torext.module_config(settings)
    torext.command_line_config()
    torext.settings['LOG_RESPONSE'] = True

    from torext.handlers import _BaseHandler

    class TestHdr(_BaseHandler):
        def get(self):
            v = '网盘'
            for i in range(10):
                v += str(random.randint(0, 9))
            #self.json_write({'百度': v})
            self.set_cookie('test', '123')
            e = Exception('蔚蓝')
            try:
                raise e
            except:
                self.json_error(401, e)

    app = TorextApp([
        ('/', TestHdr)
    ])
    app.run()
