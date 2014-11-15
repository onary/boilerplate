import os
import logging.config
import uuid
import base64
from jinja2 import Environment, FileSystemLoader
from webassets import Environment as WAEnvironment
from assets import bundles

# Make filepaths relative to settings.
location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

SITE_URL = 'http://localhost:8888/'

TEMPLATE_PATH = location("templates")

STATIC_ROOT = location('static')

DEBUG = True

APP_SETTINGS = dict(
    template_path=TEMPLATE_PATH,
    debug=DEBUG,
    static_path=STATIC_ROOT,
    login_url="/login",
    logout_url="/logout",
    cookie_secret=base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    xsrf_cookies=True,
    fb_app_id='195085404030688',
    fb_secret='b562f457a63ee85d075e547c558fe6f7',
    fb_redirect_url='%sfacebook_login' % SITE_URL,
    autoescape=None,
)

SESSION_STORE = {'pycket':
    {
        'engine': 'redis',
        'storage': {
            'host': 'localhost',
            'port': 6379,
            'db_sessions': 10,
            'db_notifications': 11,
            'max_connections': 2 ** 31,
        },
        'cookies': {
            'expires_days': 120,
        },
    }
}

APP_SETTINGS.update(SESSION_STORE)

MOTOR_CONNECT_URL = 'mongodb://localhost:27017'
DB_NAME = 'tornado'

MONGO_DB = {
    'host': 'localhost',
    'port': 27017,
    'db_name': DB_NAME,
    'reconnect_tries': 5,
    'reconnect_timeout': 2,  # in seconds
}

JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH),
                        auto_reload=DEBUG,
                        autoescape=False)

APPS = (
    'core',
    'account',
)

AUTH_USER_MODEL = 'UserModel'
AUTH_USER_COLLECTION = 'accounts'

ASSETS = WAEnvironment(STATIC_ROOT, '/static')
ASSETS.config['SASS_BIN'] = '/usr/local/bin/sass'

for k, v in bundles.iteritems():
    ASSETS.register(k, v)


# See PEP 391 and logconfig for formatting help.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main_formatter': {
            'format': '%(levelname)s:%(name)s: %(message)s '
            '(%(asctime)s; %(filename)s:%(lineno)d)',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        },
        'console_formatter': {
            'format': '%(message)s',
        },
    },
    'handlers': {
        'rotate_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': location('logs/main.log'),
            'when': 'midnight',
            'interval': 1,  # day
            'backupCount': 7,
            'formatter': 'main_formatter',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console_formatter',
            # 'filters': ['require_local_true'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['rotate_file', 'console'],
            'level': 'DEBUG',
        }
    }
}

logging.config.dictConfig(LOGGING)
