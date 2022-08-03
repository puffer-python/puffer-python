# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class AMQPMessage(db.Model, m.TimestampMixin):
    """
    Log message queue
    """
    __tablename__ = 'amqp_messages'
    _log = False

    type = db.Column(db.String(255), nullable=False)
    exchange = db.Column(db.String(255), nullable=False)
    routing_key = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text)
    sku = db.Column(db.String(255))
    attribute_set_id = db.Column(db.Integer, default=0, nullable=False)
    send_by = db.Column(db.Text)
