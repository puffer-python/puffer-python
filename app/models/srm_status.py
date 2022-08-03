# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class SRMStatus(db.Model, m.TimestampMixin):
    __tablename__ = 'srm_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(11), nullable=False)
    name = db.Column(db.String(255))
    selling_status = db.Column(db.String(255), nullable=False)
    selling_status_name = db.Column(db.String(255))