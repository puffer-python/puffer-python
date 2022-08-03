# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'phuong.h'
_logger = logging.getLogger(__name__)


class ShippingType(db.Model, m.TimestampMixin):
    __tablename__ = 'shipping_types'

    code = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

    is_active = db.Column(db.Boolean(), default=1)
    is_default = db.Column(db.Boolean(), default=0)

    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
