# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class SellableProductBundle(db.Model, m.TimestampMixin):
    __tablename__ = 'sellable_product_bundles'

    bundle_id = db.Column(db.Integer, db.ForeignKey('sellable_products.id'))  # as parent role
    sellable_product_id = db.Column(db.Integer, db.ForeignKey('sellable_products.id'))  # as children role
    created_by = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.Integer, nullable=False)

    sellable_product = db.relationship(
        'SellableProduct',
        foreign_keys=[sellable_product_id]
    )
