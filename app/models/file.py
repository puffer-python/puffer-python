# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class File(db.Model, m.TimestampMixin):
    """
    :Luu cac thong tin file
    """
    __tablename__ = 'files'

    path = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer())
    name = db.Column(db.String(255))
