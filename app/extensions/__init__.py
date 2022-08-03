# coding=utf-8
import logging

from catalog.extensions.ram.publisher import add_variant_sku_ram_publisher

from . import (
    celery,
    exceptions,
    login_manager,
    flask_restplus,
    marshmallow,
    # queue_consumer,
    signals,
    sqlalchemy_utils,
    profiling,
    request_logging
)

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


def init_app(app, **kwargs):
    """
    Extension initialization point

    :param app:
    :param kwargs:
    :return:
    """
    login_manager.init_app(app)
    profiling.init_app(app)
    # ram
    add_variant_sku_ram_publisher.init_app(
        app=app,
        ram_kafka_bootstrap_server=app.config['RAM_KAFKA_BOOTSTRAP_SERVER'],
    )


def convert_int_field(data, default=None):
    try:
        return int(data)
    except (TypeError, ValueError, AttributeError):
        return default


def convert_float_field(data, n=2, default=None):
    try:
        return round(float(data), n)
    except (TypeError, ValueError, AttributeError):
        return default
