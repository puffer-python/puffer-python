# coding=utf-8
import logging

from sqlalchemy.orm import relationship
from werkzeug.utils import cached_property
from flask_login import current_user
from sqlalchemy import String, Integer, ForeignKey, Column, Text

import config
from catalog.constants import UOM_CODE_ATTRIBUTE
from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Attribute(db.Model, m.TimestampMixin):
    """
    Lưu thông tin attribute
    """
    __tablename__ = 'attributes'

    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)
    value_type = Column(String(255), nullable=False)
    description = Column(Text)
    display_name = Column(Text)
    is_required = Column(Integer)
    is_comparable = Column(Integer)
    is_searchable = Column(Integer)
    is_filterable = Column(Integer)
    is_float = Column(Integer)
    is_unsigned = Column(Integer)
    unit_id = Column(Integer, ForeignKey('product_units.id'))
    suffix = Column(String(100), nullable=True)
    unit = relationship('ProductUnit')
    is_system = Column(Integer, nullable=True, default=0)

    products = relationship('Product', secondary='product_attribute')

    attribute_groups = relationship(
        'AttributeGroup',
        secondary='attribute_group_attribute'
    )  # type: list[m.AttributeGroup]

    attribute_description = relationship(
        'AttributeDescription',
        back_populates='attribute'
    )  # type: m.AttributeDescription

    product_variants = relationship(
        'ProductVariant',
        secondary='variant_attribute'
    )  # type: list[m.VariantAttribute]

    @cached_property
    def select_options(self):
        if self.value_type not in ['selection', 'multiple_select']:
            return []
        if self.code == UOM_CODE_ATTRIBUTE and hasattr(current_user, 'seller_id'):
            if current_user.seller_id in config.SELLER_ONLY_UOM:
                return m.AttributeOption.query.filter(
                    m.AttributeOption.seller_id == current_user.seller_id,
                    m.AttributeOption.attribute_id == self.id
                ).all() or []
            else:
                return m.AttributeOption.query.filter(
                    m.AttributeOption.attribute_id == self.id,
                    m.AttributeOption.seller_id.notin_(config.SELLER_ONLY_UOM)
                ).all() or []
        return m.AttributeOption.query.filter(
            m.AttributeOption.attribute_id == self.id
        ).all() or []

    def __str__(self):
        return f'<Attribute: {self.name}>'

    def __repr__(self):
        return f'<Attribute: {self.name}>'

    @cached_property
    def uom_attr(self):
        return m.Attribute.query.filter(
            m.Attribute.code == 'uom'
        ).first()

    @cached_property
    def name_has_unit(self):
        if self.suffix:
            return '{} ({})'.format(self.name, self.suffix)
        return self.name
