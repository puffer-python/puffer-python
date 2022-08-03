# coding=utf-8
import logging

from catalog.models import db

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class ProductsImport(db.Model):
    __tablename__ = 'products_import'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    path = db.Column(db.String(255))
    status = db.Column(db.String(255))
    key = db.Column(db.String(255))
