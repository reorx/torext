#!/usr/bin/env python
# -*- coding: utf-8 -*-

import torext
from torext.app import TorextApp


if __name__ == '__main__':
    import settings
    torext.pyfile_config(settings)

    app = TorextApp([])
    app.run()
