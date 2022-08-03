# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class ProductUnit(db.Model, m.TimestampMixin):
    __tablename__ = 'product_units'

    code = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
