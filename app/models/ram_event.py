# coding=utf-8
import logging

from sqlalchemy import func

from catalog.models import db
from catalog import models as m

__author__ = 'Dung.BV'

from catalog.models.base import BaseTimestamp

_logger = logging.getLogger(__name__)


class RamEvent(db.Model, m.TimestampMixin):
    """
    RAM events
    """
    __tablename__ = 'ram_events'

    ref = db.Column(db.String(255), nullable=False)
    parent_key = db.Column(db.String(255), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(255), nullable=False)
    retry_count = db.Column(db.Integer)
    payload = db.Column(db.Text, nullable=True)
    want_to_send_after = db.Column(BaseTimestamp, server_default=func.now(),
                                   default=func.now(), nullable=False,
                                   onupdate=func.now())
