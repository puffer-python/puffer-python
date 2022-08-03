# coding=utf-8
import json

from catalog.models import db, TimestampMixin


class Seller(db.Model, TimestampMixin):
    __tablename__ = 'sellers'

    is_manage_price = db.Column(db.Boolean)
    code = db.Column(db.String(255))
    status = db.Column(db.Integer, default=1)
    name = db.Column(db.String(255))
    english_name = db.Column(db.String(255))
    enterprise_code = db.Column(db.String(255))
    tax_number = db.Column(db.String(255))
    founding_date = db.Column(db.String(50))
    display_name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    contract_no = db.Column(db.String(255))
    extra = db.Column(db.Text)
    manual_sku = db.Column(db.Boolean, default=False)
    slogan = db.Column(db.Text)

    @property
    def extra_info(self):
        try:
            return json.loads(self.extra)
        except (TypeError, ValueError):
            return None
