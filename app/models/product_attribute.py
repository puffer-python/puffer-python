# coding=utf-8
import logging

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from catalog.models import (
    db,
    AttributeOption,
    TimestampMixin
)

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class ProductAttribute(db.Model, TimestampMixin):
    """
    Bảng lưu trữ quan hệ giữa sản phẩm và thuộc tính
    """
    __tablename__ = 'product_attribute'

    value = db.Column(db.Text)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'products.id',
            name='FK_product_attribute__product_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    product = db.relationship('Product', backref=backref('product_attributes'))

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attributes.id',
            name='FK_product_attribute__attribute_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    attribute = db.relationship('Attribute', backref=backref('product_attributes'))

    @hybrid_property
    def attribute_value(self):
        if self.attribute.value_type == 'text':
            return self.value

        options_filter = filter(
            lambda option: str(option.id) in self.value.split(','),
            self.attribute.options
        )
        options = list(options_filter)
        if self.attribute.value_type == 'selection':
            return options[0] if len(options) > 0 else None
        return options
