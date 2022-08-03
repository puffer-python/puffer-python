# coding=utf-8
import logging
from sqlalchemy import (
    ForeignKey,
    func
)

from catalog.models import db

__author__ = 'Thanh.NK'
_logger = logging.getLogger(__name__)


class EditingStatusHistory(db.Model):
    """
    Log các thông tin editing của sản phẩm
    """
    __tablename__ = 'editing_status_histories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    editing_status = db.Column(db.String(255))
    state = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, default=func.now())
    created_by = db.Column(db.String(20))
    comment = db.Column(db.String(255))
    reason_type = db.Column(db.String(255))

    product_id = db.Column(
        db.Integer,
        ForeignKey(
            'products.id',
            name='FK_editing_status_history_product_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False
    )
