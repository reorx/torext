PROJECT = '{project_name}'

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

LOGGING = {
    '': {
        'level': 'INFO',
        'propagate': 1,
        'type': 'stream',
        'color': True,
        'fmt': ' %(message)s'
    }
}

LOG_REQUEST = False

LOG_RESPONSE = False

TIME_ZONE = 'Asia/Shanghai'

STATIC_PATH = 'static'

TEMPLATE_PATH = 'template'

UNLOG_URLS = [
    '/favicon.ico',
]
