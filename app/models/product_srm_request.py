# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class ProductSrmRequest(db.Model, m.TimestampMixin):
    """
    Lưu trữ url file upload
    """
    __tablename__ = 'product_srm_request'

    product_id = db.Column(db.Integer(), nullable=False)
    action = db.Column(db.String(255), default='create')
    request_body = db.Column(db.Text())
    is_send = db.Column(db.Integer(), default=0)
    last_sent = db.Column(db.TIMESTAMP())
    response_body = db.Column(db.Text())
    response_code = db.Column(db.Integer())
