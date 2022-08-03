# coding=utf-8

from catalog.models import (
    db,
)


class TblIndex(db.Model):
    __tablename__ = 'tblIndex'

    ntIndex = db.Column(db.Integer, primary_key=True)
