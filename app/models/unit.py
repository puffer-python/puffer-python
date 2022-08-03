# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Unit(db.Model, m.TimestampMixin):
    """
    Unit variations
    """
    __tablename__ = 'units'

    code = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
    seller_id = db.Column(db.Integer, nullable=False)
    display_name = db.Column(db.String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
