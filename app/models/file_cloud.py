# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class FileCloud(db.Model, m.TimestampMixin):
    """
    :Luu cac thong tin file tren cloud
    """
    __tablename__ = 'file_cloud'

    public_id = db.Column(db.String(255))
    url = db.Column(db.String(255))
    file_id = db.Column(db.Integer)
