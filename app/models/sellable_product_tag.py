# coding=utf-8

from sqlalchemy.orm import backref
from sqlalchemy.ext.hybrid import hybrid_property
from catalog.models import (
    db,
    TimestampMixin
)
from catalog import models as m


class SellableProductTag(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_tags'

    sellable_product_id = db.Column(db.Integer, nullable=False, unique=False)
    sku = db.Column(db.String(100), nullable=False, unique=False)
    tags = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

