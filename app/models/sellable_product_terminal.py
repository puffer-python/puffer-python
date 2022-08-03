# coding=utf-8

from sqlalchemy.orm import backref
from sqlalchemy import UniqueConstraint
from catalog.models import (
    db,
    TimestampMixin
)


class SellableProductTerminal(db.Model, TimestampMixin):
    __tablename__ = 'sellable_product_terminal'
    __table_args__ = (
        UniqueConstraint('terminal_id', 'sellable_product_id'),
    )

    sellable_product_id = db.Column(db.Integer,
                                    db.ForeignKey('sellable_products.id'),
                                    nullable=False)
    terminal_id = db.Column(db.Integer,
                            db.ForeignKey('terminals.id'),
                            nullable=False)
    terminal_code = db.Column(db.String(255))
    terminal_type = db.Column(db.String(255))
    meta_title = db.Column(db.Text)
    meta_keyword = db.Column(db.Text)
    meta_description = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    sellable_product = db.relationship('SellableProduct', backref=backref('seo'))
    terminal = db.relationship('Terminal', backref=backref('seo'))
    apply_seller_id = db.Column(db.Integer())
    on_off_status = db.Column(db.String(45))
