# coding=utf-8

from catalog.models import (
    db,
    TimestampMixin
)


class SellableProductBarcode(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_barcodes'

    sellable_product_id = db.Column(db.Integer, nullable=False, unique=False)
    barcode = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.String(255))

    __table_args__ = (
        db.Index('sellable_product_barcodes__sku_id', sellable_product_id),
        db.Index('sellable_product_barcodes__barcode', barcode),
    )
