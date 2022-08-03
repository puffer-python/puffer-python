# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Color(db.Model, m.TimestampMixin):
    """
    Lưu thông tin màu sắc sản phẩm
    """
    __tablename__ = 'colors'

    code = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)

    def __str__(self):
        return self.name

