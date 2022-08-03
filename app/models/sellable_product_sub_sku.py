# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'dung.bv'
_logger = logging.getLogger(__name__)


class SellableProductSubSku(db.Model, m.TimestampMixin):
    __tablename__ = 'sellable_product_sub_sku'

    sellable_product_id = db.Column(db.Integer,
                                    db.ForeignKey('sellable_products.id'),
                                    nullable=False)

    sellable_product = db.relationship('SellableProduct')

    sub_sku = db.Column(db.String(255), nullable=False, unique=True)

    is_active = db.Column(db.Boolean(), default=1)

    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
