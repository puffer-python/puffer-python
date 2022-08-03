import logging
import os

from dotenv import load_dotenv

__author__ = 'Kien'
_logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__)
))
# The environment to run this config. This value will affect to the
# configuration loading
#
# it can be: dev, test, stag, prod
_DOT_ENV_PATH = os.path.join(ROOT_DIR, '.env')
load_dotenv(_DOT_ENV_PATH)
ENV_MODE = os.environ.get('ENV_MODE', '').upper()

DEBUG = os.getenv('FLASK_DEBUG') not in ('0', None)
TESTING = False
LOGGING_CONFIG_FILE = os.path.join(ROOT_DIR, 'etc', 'logging.ini')

FLASK_APP_SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious_secret_key')

MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', None)
MYSQL_DATABASE_TEST = os.getenv('MYSQL_DATABASE_TEST', 'database')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')
MYSQL_USER = os.getenv('MYSQL_USER', 'user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'secret')

USER_API = os.getenv('USER_API', 'https://id.teko.vn/userinfo')
IAM_API = os.getenv('IAM_API')
SELLER_API = os.getenv('SELLER_API', 'http://seller-core-api.seller-service')

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, 3306, MYSQL_DATABASE
)
# SQLALCHEMY_DATABASE_URI = 'sqlite://'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_COMMIT_ON_TEARDOWN = False

MAX_IMPORT_FILE_PENDING = int(os.getenv('MAX_IMPORT_FILE_PENDING', '10'))

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

SRM_SERVICE_URL = os.getenv('SRM_API', 'http://dev.api-srm.phongvu.vn')
SYNC_CATEGORY_TO_SRM_DELAY_TIME = int(os.getenv('SYNC_CATEGORY_TO_SRM_DELAY_TIME', 3600))
# default to retry sync to SRM in 2 days
SYNC_CATEGORY_TO_SRM_REPEAT_TIME = int(os.getenv('SYNC_CATEGORY_TO_SRM_REPEAT_TIME', 48))

AMQP_HOST = os.getenv('AMQP_HOST', None)
AMQP_PORT = os.getenv('AMQP_PORT', None)
AMQP_USER = os.getenv('AMQP_USER', None)
AMQP_PASSWORD = os.getenv('AMQP_PASSWORD', None)
AMQP_VHOST = os.getenv('AMQP_VHOST', None)

TEKO_AMQP_URL = 'amqp://{}:{}@{}:{}/{}'.format(
    AMQP_USER, AMQP_PASSWORD, AMQP_HOST, AMQP_PORT, AMQP_VHOST
)

MEDIA_IMPORT_DIR = os.path.join(ROOT_DIR, 'media', 'import')
MEDIA_BRAND_DIR = os.path.join('media', 'brands')
BRAND_LOGO_STORAGE_API = os.getenv('BRAND_LOGO_STORAGE_API', 'http://localhost:8083/brands')
ERROR_404_HELP = False

USER_API_V2 = os.getenv('USER_API_V2', 'https://oauth.develop.tekoapis.net/userinfo')
PPM_API = os.getenv('PPM_API', 'https://ppm-test.develop.tekoapis.net/api')
PPM_BATCH_PRICE_SCHEDULE_API = f'{PPM_API}/batch-price-schedules'
FILE_API = os.getenv('FILE_API', 'http://files-core-api.files-service')
NOTI_SERVICE_DOMAIN = {
    'Domain': os.getenv('NOTI_SERVICE_DOMAIN_DOMAIN', 'https://notification.saas.tekoapis.net'),
    'TemplateId': os.getenv('NOTI_SERVICE_DOMAIN_TEMPLATE_ID', 1146),
    'Brand': os.getenv('NOTI_SERVICE_DOMAIN_BRAND ', 'noreply@teko.vn'),
    'Token': os.getenv('NOTI_SERVICE_DOMAIN_TOKEN ', 'teko_erp_token'),
}

BASE_IMAGE_URL = os.getenv('BASE_IMAGE_URL', 'https://lh3.googleusercontent.com')

CACHE_REDIS_URL = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379')
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')

CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', False)
SELLER_GATEWAY_INTERNAL_URL = os.getenv('SELLER_GATEWAY_INTERNAL_URL', None)

# list of internal service urls, separated by commas
INTERNAL_HOST_URLS = os.getenv('INTERNAL_HOST_URLS', ['127.0.0.1:5000'])

MAGENTO_HOST = os.getenv('MAGENTO_HOST', 'https://stg.tekshop.vn')

# AMP
APM_SERVER_URL = os.getenv('APM_SERVER_URL')
ELASTIC_APM = {
    'SERVER_URL': APM_SERVER_URL,
    'SERVICE_NAME': f'catalog-api-{ENV_MODE}',
    'SECRET_TOKEN': os.getenv('APM_SECRET_TOKEN') or None,
    'DEBUG': True,
    'TRANSACTIONS_IGNORE_PATTERNS': ['^OPTIONS '],
    'ELASTIC_APM_ENABLED': True if APM_SERVER_URL else False,
    'ELASTIC_APM_ENVIRONMENT': ENV_MODE
}

# The Sellers only use their UOM
# 4: VinMart
# 18: Masan Consumer
SELLER_ONLY_UOM = [4, 18]

# RAM
RAM_KAFKA_BOOTSTRAP_SERVER = os.getenv('RAM_KAFKA_BOOTSTRAP_SERVER', 'confluent-kafka-cp-kafka.confluent-kafka:9092')
RAM_KAFKA_CONSUMER_GROUP_NAME = os.getenv('RAM_KAFKA_CONSUMER_GROUP_NAME', 'catalog-ram-kafka')
RAM_KAFKA_ENABLE_ADD_VARIANT_SKU_PUBLISHER = True


def _env(name, default):
    """ Get configuration from environment in priorities:
      1. the env var with prefix of $ENV_MODE
      2. the env var with the same name (in upper case)
      3. the default value

    :param str name: configuration name
    :param default: default value
    """

    def _bool(val):
        if not val:
            return False
        return val not in ('0', 'false', 'no')

    # make sure configuration name is upper case
    name = name.upper()

    # try to get value from env vars
    val = default
    for env_var in ('%s_%s' % (ENV_MODE, name), name):
        try:
            val = os.environ[env_var]
            break
        except KeyError:
            pass
    else:
        env_var = None

    # convert to the right types
    if isinstance(default, bool):
        val = _bool(val)
    return env_var, val


_IGNORED_CONFIG = (
    'ROOT_DIR',
    'STATIC_DIR',
    'ENV_MODE',
)

# rewrite all configuration with environment variables
_vars = list(locals().keys())
for name in _vars:
    if name in _IGNORED_CONFIG:
        continue
    if not name.startswith('_') and name.isupper():
        env_var, val = _env(name, locals()[name])
        locals()[name] = val
