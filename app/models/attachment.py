# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Attachment(db.Model, m.TimestampMixin):
    """
    Lưu trữ url file upload
    """
    __tablename__ = 'attachments'

    url = db.Column(db.Text)
    name = db.Column(db.String(255))

    sellable_product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'sellable_products.id',
            name='FK_attachments__sellable_products',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    sellable_product = db.relationship(
        'SellableProduct',
        backref='attachments'
    )  # type: m.SellableProduct
