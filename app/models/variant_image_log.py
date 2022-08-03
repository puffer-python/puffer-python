# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Minh.ND1'
_logger = logging.getLogger(__name__)


class VariantImageLog(db.Model, m.TimestampMixin):
    __tablename__ = 'variant_image_logs'

    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'))

    input_url = db.Column(db.Text)
    success_url = db.Column(db.Text)

    result = db.Column(db.String(255))
    request_id = db.Column(db.String(40))
