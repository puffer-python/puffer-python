# coding=utf-8

from catalog.models import (
    db,
    TimestampMixin
)


class SellableProductPrice(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_price'

    sellable_product_id = db.Column(
        db.Integer,
        db.ForeignKey('sellable_products.id')
    )
    terminal_group_ids = db.Column(db.String(255), nullable=True)
    selling_status = db.Column(db.Integer, nullable=False, default=1)
    selling_price = db.Column(db.Integer, nullable=False, default=1)
    tax_out_code = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.String(255), nullable=True)
