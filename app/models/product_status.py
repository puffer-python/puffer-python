# coding=utf-8
from catalog.models import db


class ProductStatus(db.Model):
    """
    Lưu các thông tin về status của sản phẩm
    """
    __tablename__ = 'product_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    code = db.Column(db.String(255), nullable=False, index=True)
    labels = db.relationship('ProductLabel')


class ProductLabel(db.Model):
    """
    Lưu các thông tin về label của sản phẩm
    """
    __tablename__ = 'product_labels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), db.ForeignKey('product_status.code'),
                       nullable=False)
