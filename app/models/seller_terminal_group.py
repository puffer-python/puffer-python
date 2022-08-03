from catalog.models import db
from catalog.models import TimestampMixin


class SellerTerminalGroup(db.Model, TimestampMixin):
    __tablename__ = 'seller_terminal_groups'

    terminal_group_id = db.Column(db.Integer(), db.ForeignKey('terminal_groups.id'))
    seller_id = db.Column(db.Integer(), db.ForeignKey('sellers.id'))
    is_owner = db.Column(db.Boolean())
    is_requested_approval = db.Column(db.Boolean())
