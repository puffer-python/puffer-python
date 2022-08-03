# coding=utf-8
import logging

from catalog.models import db, TimestampMixin

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class Provider(db.Model, TimestampMixin):
    __tablename__ = 'providers'

    name = db.Column(db.Text)
    display_name = db.Column(db.Text)
    code = db.Column(db.Text)
    is_active = db.Column(db.Boolean)
    created_by = db.Column(db.String(255))
