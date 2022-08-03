# coding=utf-8
import logging
from datetime import timedelta

from sqlalchemy.types import DateTime, TypeDecorator

import flask_sqlalchemy as _fs
import sqlalchemy as _sa
import flask_migrate as _fm
from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr

__author__ = 'Kien'

import config

_logger = logging.getLogger(__name__)


class BaseTimestamp(TypeDecorator):
    impl = DateTime()

    def process_result_value(self, value, dialect):
        if value is not None:
            return value + timedelta(hours=7)
        return value


class SQLAlchemy(_fs.SQLAlchemy):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        options["pool_pre_ping"] = True


class TimestampMixin(object):
    """
    Adds `created_at` and `updated_at` common columns to a derived
    declarative model.
    """

    @declared_attr
    def id(self):
        return _sa.Column(_sa.Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def created_at(self):
        return _sa.Column(BaseTimestamp, server_default=func.now(),
                          default=func.now(), nullable=False)

    @declared_attr
    def updated_at(self):
        return _sa.Column(
            BaseTimestamp, server_default=func.now(),
            default=func.now(), nullable=False,
            onupdate=func.now())


db = SQLAlchemy()
migrate = _fm.Migrate(db=db)


def init_app(app, **kwargs):
    """
    Extension initialization point
    :param flask.Flask app: the app
    :param kwargs:
    :return:
    """
    db.app = app
    db.init_app(app)
    migrate.init_app(app)
    _logger.info('Start app in {env} environment with database: {db}'.format(
        env=app.config['ENV_MODE'],
        db=app.config['MYSQL_DATABASE']
    ))
