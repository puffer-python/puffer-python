# coding=utf-8
import logging

from catalog.models import db, TimestampMixin

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class IAMUser(db.Model, TimestampMixin):
    __tablename__ = 'iam_users'

    iam_id = db.Column(db.String(255))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    access_token = db.Column(db.Text)
    seller_id = db.Column(
        db.Integer,
        db.ForeignKey('sellers.id')
    )       #TODO: link to nulti seller
    seller_ids = db.Column(db.String(255))
    seller = db.relationship('Seller', backref='iam_users', lazy='joined')

    def check_and_update_seller_id(self, seller_id):
        if self.seller_ids == '0':
            from catalog.services import seller as seller_srv       #TODO: move to top
            existed = seller_srv.get_seller_by_id(seller_id)
            return bool(existed)

        available_ids = self.seller_ids.split(',') if self.seller_ids else []

        if str(seller_id) in available_ids:
            self.seller_id = seller_id
            db.session.commit()
            return True

        return False
