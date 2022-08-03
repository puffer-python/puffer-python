# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class ShippingPolicy(db.Model, m.TimestampMixin):
    """
    Lưu thông tin attribute group
    """
    __tablename__ = 'shipping_policy'

    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean)
    shipping_type = db.Column(db.String(255), nullable=False)

    providers = db.relationship('ShippingPolicyMapping', lazy='subquery')
    categories = db.relationship('MasterCategory', secondary='shipping_policy_mapping', lazy='subquery')

    # Add relationship to misc table to prevent calling query to get misc for each shipping policy element
    misc = db.relationship('Misc', foreign_keys=[shipping_type], primaryjoin='and_(Misc.code == ShippingPolicy.shipping_type, Misc.type == "shipping_type")', lazy='subquery')

    @property
    def shipping_type_name(self):
        # Remove call query to Misc table for each element
        if self.misc:
            return self.misc.name
        else:
            return self.shipping_type


class ShippingPolicyMapping(db.Model, m.TimestampMixin):
    """
    Mapping shipping policies <=> providers and categories
    """
    __tablename__ = 'shipping_policy_mapping'

    policy_id = db.Column(
        db.Integer,
        db.ForeignKey('shipping_policy.id'),
        nullable=False
    )

    provider_id = db.Column(
        db.Integer,
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('master_categories.id'),
        nullable=False
    )
    category = db.relationship('MasterCategory', foreign_keys=[category_id, ])

