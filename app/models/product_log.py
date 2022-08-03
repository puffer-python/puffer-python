# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Shyaken'
_logger = logging.getLogger(__name__)


class ProductLog(db.Model, m.TimestampMixin):
    __tablename__ = 'product_logs'
    _log = False

    updated_by = db.Column(db.String(255))
    sku = db.Column(db.String(255), db.ForeignKey('sellable_products.sku'),
                    nullable=False)

    old_data = db.Column(db.Text)
    new_data = db.Column(db.Text)

    product = db.relationship('SellableProduct')
