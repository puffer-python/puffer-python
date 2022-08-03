# coding=utf-8
import logging
from sqlalchemy import func

from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class LogImportFile(db.Model):
    """
    Lưu log import file
    """
    __tablename__ = 'logs_import_file'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(255))
    name_file = db.Column(db.String(255))
    log = db.Column(db.Text)
    status = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, server_default=func.now(),
                           default=func.now())


class LogEditProduct(db.Model):
    """
    Lưu log edit sản phẩm
    """
    __tablename__ = 'log_edit_product'
    _log = False

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    updated_by_email = db.Column(db.String(255), nullable=True)
    updated_by_name = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(),
                           default=func.now())


class LogEditProductConfigurable(db.Model):
    __tablename__ = 'log_edit_product_configurable'
    _log = False

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    configurable_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(),
                           default=func.now())
