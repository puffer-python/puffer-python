# coding=utf-8

from catalog.models import db


class SellerTerminal(db.Model):
    __tablename__ = 'sellers_terminals'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer)
    terminal_id = db.Column(db.Integer)
    is_requested_approval = db.Column(db.Boolean(), default=0)
    is_owner = db.Column(db.Boolean(), default=0)
