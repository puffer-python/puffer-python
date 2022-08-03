# coding=utf-8
import logging

import os

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Brand(db.Model, m.TimestampMixin):
    """
    Lưu thông tin thương hiệu
    """
    __tablename__ = 'brands'

    code = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean(), default=1)
    doc_request = db.Column(db.Integer, default=0)
    approved_status = db.Column(db.Integer, default=1)
    path = db.Column(db.Text)
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
    internal_code = db.Column(db.String(10))
