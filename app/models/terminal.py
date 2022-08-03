# coding=utf-8

from catalog.models import db


class Terminal(db.Model):
    __tablename__ = 'terminals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    platform = db.Column(db.String(30), nullable=False)
    full_address = db.Column(db.String(511), nullable=False)
    is_active = db.Column(db.Boolean(), default=1)
    is_requested_approval = db.Column(db.Boolean(), default=0)
    updated_at = db.Column(db.DateTime())

    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'),
                          nullable=False)
    seller = db.relationship('Seller', backref='terminals')

    groups = db.relationship('TerminalGroup', secondary='terminal_group_terminal')
