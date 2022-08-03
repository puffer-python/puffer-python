# coding=utf-8

from catalog.models import db


class SellingStatus(db.Model):
    __tablename__ = 'selling_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    code = db.Column(db.String(30), index=True)
    config = db.Column(db.String(255))
