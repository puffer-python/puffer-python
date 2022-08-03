# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Misc(db.Model, m.TimestampMixin):
    """
    Lưu các thông tin khác của sản phẩm
    """
    __tablename__ = 'misc'

    name = db.Column(db.String(255))
    type = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(101), index=True)
    config = db.Column(db.Text)
    position = db.Column(db.Integer)
