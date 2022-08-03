# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class User(db.Model, m.TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'))
    seller = db.relationship('Seller', backref='users')
