# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class AttributeGroup(db.Model, m.TimestampMixin):
    """
    Lưu thông tin attribute group
    """
    __tablename__ = 'attribute_groups'

    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer)
    parent_id = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, nullable=False, default=1)
    is_flat = db.Column(db.Boolean)
    path = db.Column(db.String(255))
    system_group = db.Column(db.Boolean)

    attribute_set_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attribute_sets.id',
            name='FK_attribute_groups_attribute_set_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    attribute_set = db.relationship(
        'AttributeSet',
        backref='groups'
    )  # type: m.AttributeSet

    attributes = db.relationship(
        'Attribute',
        secondary='attribute_group_attribute'
    )  # type: list[m.Attribute]
