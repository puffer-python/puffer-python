# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class VariantImage(db.Model, m.TimestampMixin):
    """
    Storage the images of products
    """
    __tablename__ = 'variant_images'

    name = db.Column(db.Text)
    url = db.Column(db.Text)
    path = db.Column(db.Text)
    label = db.Column(db.String(255), default='', nullable=True)
    priority = db.Column(db.Integer, default=0, nullable=False)
    is_displayed = db.Column(db.Integer, default=True)
    status = db.Column(db.Integer, default=1)
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

    product_variant_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'product_variants.id',
            name='FK_variant_images__product_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False
    )

    product_variant = db.relationship(
        'ProductVariant',
        backref='images'
    )  # type: m.ProductVariant
