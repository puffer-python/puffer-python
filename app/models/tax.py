#coding=utf-8

from catalog.models import db


class Tax(db.Model):
    __tablename__ = 'taxes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    label = db.Column(db.String(50))
    amount = db.Column(db.Float)
    description = db.Column(db.String(255))
