PROJECT = '{project_name}'

LOCALE = 'en_US'

PROCESSES = 1

PORT = 8000

DEBUG = True

LOGGING = 'INFO'

LOG_REQUEST = True

LOG_RESPONSE = False

TIME_ZONE = 'Asia/Shanghai'

STATIC_PATH = 'static'

TEMPLATE_PATH = 'template'

# You can use jinja2 instead
TEMPLATE_ENGINE = 'tornado'

LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]
