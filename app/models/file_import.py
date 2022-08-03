# coding=utf-8
import logging
import os

from catalog import models as m
from catalog.models import db

__author__ = 'thiem.nv'
_logger = logging.getLogger(__name__)


class FileImport(db.Model, m.TimestampMixin):
    """
    Lưu danh sách lịch sử import
    """
    __tablename__ = 'file_imports'

    type = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255))
    success_path = db.Column(db.String(255))
    status = db.Column(db.String(255))
    note = db.Column(db.Text)
    total_row = db.Column(db.Integer)
    total_row_success = db.Column(db.Integer)
    created_by = db.Column(db.String(255))
    attribute_set_id = db.Column(db.Integer)
    seller_id = db.Column(db.Integer)
    platform_id = db.Column(db.Integer)
