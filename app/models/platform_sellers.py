# coding=utf-8
import logging

from catalog.models import db, TimestampMixin

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class PlatformSellers(db.Model, TimestampMixin):
    __tablename__ = 'platform_sellers'

    platform_id = db.Column(db.Integer())
    seller_id = db.Column(db.Integer())
    is_default = db.Column(db.Boolean)
    is_owner = db.Column(db.Boolean)

    __table_args__ = (
        db.Index('platform_sellers__platform_id', platform_id),
        db.Index('platform_sellers__seller_id', seller_id),
    )
