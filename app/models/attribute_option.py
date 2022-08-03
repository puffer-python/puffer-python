# coding=utf-8
import logging

from sqlalchemy.orm import backref
from werkzeug.utils import cached_property

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class AttributeOption(db.Model, m.TimestampMixin):
    """
    Lưu thông tin thuộc tính
    """
    __tablename__ = 'attribute_options'

    value = db.Column(db.String(255))
    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attributes.id',
            name='FK_attribute_option__attribute_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False
    )
    attribute = db.relationship('Attribute', backref=backref('options'))

    unit_id = db.Column(db.Integer(), db.ForeignKey('product_units.id'))
    unit = db.relationship('ProductUnit')

    seller_id = db.Column(db.Integer(), default=0)

    code = db.Column(db.String(100))
    display_value = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))
    priority = db.Column(db.Integer(), nullable=False, default=0)

    @cached_property
    def display_code(self):
        if not self.code or self.code == '':
            return str(self.id)
        return self.code
