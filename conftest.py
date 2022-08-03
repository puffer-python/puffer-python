# coding=utf-8
import logging
import os

import pytest
import requests

import config

from datetime import datetime
from operator import itemgetter

__author__ = 'Kien'

_logger = logging.getLogger(__name__)

TEST_DIR = os.path.join(config.ROOT_DIR, 'tests')

config.CACHE_TYPE = 'simple'
config.TESTING = True

config.CELERY_BROKER_URL = 'memory://'
config.CELERY_RESULT_BACKEND = 'db+sqlite://'
config.BROKER_URL = 'memory://'


@pytest.fixture(scope='session')
def app(request):
    from catalog import create_app

    config.DEBUG = False
    app = create_app()
    from catalog.extensions import flask_cache
    flask_cache.init_cache(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['MEDIA_IMPORT_DIR'] = os.path.join(config.ROOT_DIR, 'media', 'import', 'tests')

    return app
