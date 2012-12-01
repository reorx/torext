PROJECT = 'tortest'

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

LOGGING = {
    'level': 'INFO',
    'propagate': 1,
    'color': True,
    'contentfmt': '-> %(message)s'
}

LOG_REQUEST = False

LOG_RESPONSE = False

TIME_ZONE = 'Asia/Shanghai'

STATIC_PATH = 'static'

TEMPLATE_PATH = 'template'

LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]
