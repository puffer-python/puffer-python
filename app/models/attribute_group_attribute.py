# coding=utf-8
import logging
from sqlalchemy import func
from sqlalchemy.orm import backref

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class AttributeGroupAttribute(db.Model, m.TimestampMixin):
    """
    Bảng phụ lưu quan hệ giữa attribute group và attribute
    """
    __tablename__ = 'attribute_group_attribute'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    priority = db.Column(db.Integer)
    highlight = db.Column(db.Integer)
    text_before = db.Column(db.Text)
    text_after = db.Column(db.Text)
    is_displayed = db.Column(db.Integer, default=1)
    is_variation = db.Column(db.Integer, default=0)
    variation_display_type = db.Column(db.Text(255))
    variation_priority = db.Column(db.Integer, nullable=True)

    @property
    def group_level1_id(self):
        try:
            path = self.attribute_group.path
            if path:
                if '/' in path:
                    level1_id = path.split('/')[0]
                    return int(level1_id)
                return int(path)
        except AttributeError:
            return None

    attribute_group_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attribute_groups.id',
            name='FK_attribute_group_attribute__attribute_group_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),

        nullable=False,
    )
    attribute_group = db.relationship(
        'AttributeGroup',
        backref=backref('attribute_group_attribute')
    )  # type: m.AttributeGroup

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attributes.id',
            name='FK_attribute_group_attribute__attribute_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False,
    )
    attribute = db.relationship(
        'Attribute',
        backref=backref('attribute_group_attribute')
    )  # type: m.Attribute
