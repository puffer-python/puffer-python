# coding=utf-8

from sqlalchemy.orm import backref
from sqlalchemy import UniqueConstraint
from catalog.models import (
    db,
    TimestampMixin
)


class SellableProductSeoInfoTerminal(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_seo_info_terminal'
    __table_args__ = (
        UniqueConstraint('terminal_id', 'sellable_product_id'),
    )

    sellable_product_id = db.Column(db.Integer,
                                    db.ForeignKey('sellable_products.id'),
                                    nullable=False)
    terminal_id = db.Column(db.Integer,
                            db.ForeignKey('terminals.id'),
                            nullable=False)
    terminal_code = db.Column(db.String(45))

    display_name = db.Column(db.String(255))
    meta_title = db.Column(db.Text)
    meta_keyword = db.Column(db.Text)
    meta_description = db.Column(db.Text)
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    url_key = db.Column(db.Text)

    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

    sellable_product = db.relationship('SellableProduct')
    terminal = db.relationship('Terminal')

    @property
    def static_url_key(self):
        return self.url_key or self.sellable_product.product_variant.url_key
