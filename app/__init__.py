# coding=utf-8
import logging
import logging.config
import os

import flask
from werkzeug.middleware.proxy_fix import ProxyFix

import config
from catalog.extensions import time_logging
from catalog.extensions import celery as _celery, exceptions as exc, flask_cache
from catalog.extensions.request_logging import log_request
from ram.v1_0.producer.ram_producer import RamProducer

from . import utils, constants, models, services, validators, extensions, api

__author__ = 'DUNG.BV'

from .constants import UOM_CODE_ATTRIBUTE

_logger = logging.getLogger(__name__)


def _after_request(response):
    origin = flask.request.headers.get('Origin')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers[
        'Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Content-Disposition, X-USER-ID, X-SELLER-ID'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response


def create_app():
    """
    Create Flask app with various configurations
    :rtype: flask.Flask
    """

    def load_app_config(app):
        """
        Load app configuration
        :param flask.Flask app:
        :return:
        """
        app.config.from_object(config)
        app.config.from_pyfile('test_ram_config.py', silent=True)
        app.json_encoder = extensions.sqlalchemy_utils.JSONEncoder

    app = flask.Flask(
        __name__,
        instance_relative_config=True,
        instance_path=os.path.join(config.ROOT_DIR, 'instance'),
        static_folder=os.path.join(config.ROOT_DIR, 'media'),
        static_url_path='/media'
    )
    load_app_config(app)

    # setup logging
    logging.config.fileConfig(app.config['LOGGING_CONFIG_FILE'],
                              disable_existing_loggers=False)

    if app.debug:
        app.wsgi_app = time_logging.time_logging(app.wsgi_app)
        time_logging.enable_sqlalchemy_runtime_logging()

    # setup cross origin sharing
    app.after_request(_after_request)

    app.secret_key = config.FLASK_APP_SECRET_KEY
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # sub-modules initialization
    models.init_app(app)
    api.init_app(app)
    extensions.init_app(app)

    return app


def register_telemetry(flask_app):
    from prometheus_client import multiprocess
    from prometheus_client.core import CollectorRegistry
    from prometheus_flask_exporter import PrometheusMetrics

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry, path=os.environ.get(
        'prometheus_multiproc_dir', '/tmp'))
    return PrometheusMetrics(
        flask_app, group_by='url_rule', registry=registry,
        static_labels={
            'app': "catalog-api",
        }, defaults_prefix='teko')


app = create_app()
metrics = register_telemetry(app)
celery = extensions.celery.make_celery(app)
cache = flask_cache.init_cache(app)
producer = RamProducer()

from catalog import biz
from catalog import system
