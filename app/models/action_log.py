# coding=utf-8
import logging
from sqlalchemy import func

from catalog.models import db

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    _log = False

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, default=0)
    action = db.Column(db.String(255))
    object = db.Column(db.String(255))
    object_id = db.Column(db.Integer)
    object_data = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now(),
                           default=func.now(), nullable=False)
