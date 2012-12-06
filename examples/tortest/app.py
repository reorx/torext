#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from torext.app import TorextApp
from torext.handlers import _BaseHandler


app = TorextApp()


class TestHdr(_BaseHandler):
    def get(self):
        v = '网盘'
        for i in range(10):
            v += str(random.randint(0, 9))
        #return self.write(v)
        #return self.json_write({'百度': v})

        self.set_cookie('test', '123')
        e = Exception('蔚蓝')
        l = []
        l[1]
        return
        try:
            raise e
        except:
            self.json_error(401, e)


if __name__ == '__main__':
    import settings

    app.module_config(settings)
    app.command_line_config()
    app.settings['LOG_RESPONSE'] = True

    app.add_handler('/', TestHdr)

    app.run()
