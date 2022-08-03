# coding=utf-8

from catalog.models import (
    db,
    TimestampMixin
)


class ProductCategory(db.Model, TimestampMixin):
    __tablename__ = 'product_categories'

    product_id = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_by = db.Column(db.String(255))

    category = db.relationship('Category', backref='product_categories')

    __table_args__ = (
        db.Index('product_categories__product_id', product_id),
        db.Index('product_categories__category_id', category_id),
    )