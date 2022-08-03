# coding=utf-8
import logging

import sqlalchemy as _sa
from sqlalchemy.ext.declarative.base import declared_attr

from catalog import models
from catalog.models import db

__author__ = 'Minh.ND'
_logger = logging.getLogger(__name__)


class RequestLog(db.Model, models.TimestampMixin):
    __tablename__ = 'request_logs'

    request_ip = db.Column(db.String(15))
    request_host = db.Column(db.String(255))
    request_method = db.Column(db.String(15))
    request_path = db.Column(db.Text())
    request_params = db.Column(db.Text())
    request_body = db.Column(db.Text())
    response_body = db.Column(db.Text())
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
