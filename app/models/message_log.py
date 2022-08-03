# coding=utf-8
import enum
import logging
import json
from datetime import datetime

from catalog.models import db

_logger = logging.getLogger(__name__)


class MsgLog(db.Model):
    __tablename__ = 'message_logs'
    _log = False

    class Status(enum.Enum):
        """Status of a message"""
        init = 'init'
        ok = 'ok'
        failed = 'failed'
        retried = 'retried'
        cancelled = 'cancelled'
        ignored = 'ignored'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exchange = db.Column(db.String(255))
    queue = db.Column(db.String(255))
    routing_key = db.Column(db.String(128), index=True)
    body_raw = db.Column(db.TEXT)
    error_message = db.Column(db.TEXT)
    log = db.Column(db.TEXT)
    properties = db.Column(db.TEXT)
    status = db.Column(db.Enum(Status),
                       default=Status.init)
    action = db.Column(db.String(255), default='receive')
    created_at = db.Column(db.DATETIME, default=datetime.now)

    @property
    def body(self):
        return json.loads(self.body_raw)
