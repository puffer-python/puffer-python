# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class SellableProductSeoInfo(db.Model, m.TimestampMixin):
    __tablename__ = 'sellable_product_seo_info'

    sellable_product_id = db.Column(
        db.Integer, db.ForeignKey('sellable_products.id')
    )  # as children role

    sellable_product = db.relationship(
        'SellableProduct',
        foreign_keys=[sellable_product_id]
    )
    short_description = db.Column(db.Text())
    description = db.Column(db.Text())
    meta_title = db.Column(db.Text())
    meta_keyword = db.Column(db.Text())
    meta_description = db.Column(db.Text())
