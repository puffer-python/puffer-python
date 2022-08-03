# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class AttributeDescription(db.Model, m.TimestampMixin):
    """
    Lưu mô tả thuộc tính
    """
    __tablename__ = 'attribute_description'

    short_description_priority = db.Column(db.Integer)
    short_description_before = db.Column(db.String(255))
    short_description_after = db.Column(db.String(255))
    short_description_default = db.Column(db.Text)

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attributes.id',
            name='FK_attribute_description__attribute_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False
    )

    attribute = db.relationship(
        'Attribute',
        back_populates='attribute_description',
        uselist=False
    )  # type: m.Attribute
