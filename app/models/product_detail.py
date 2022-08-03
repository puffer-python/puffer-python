# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class ProductDetail(db.Model, m.TimestampMixin):
    """
    Lưu mô tả sản phẩm
    """
    __tablename__ = 'product_details'

    sku = db.Column(db.String(255), db.ForeignKey('sellable_products.sku'),
                    nullable=False)
    data = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(255))
    catalog_status_code = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

    product = db.relationship('SellableProduct')
