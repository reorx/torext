PROJECT = 'torext_project'

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

LOGGING = {
    'level': 'DEBUG',
    'propagate': 1,
    'color': True,
    'contentfmt': '-> %(message)s'
}

LOG_REQUEST = False

LOG_RESPONSE = False

TIME_ZONE = 'Asia/Shanghai'

LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]
