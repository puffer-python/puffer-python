from catalog.models import db
from catalog.models import TimestampMixin


class TerminalGroup(db.Model, TimestampMixin):
    __tablename__ = 'terminal_groups'

    code = db.Column(db.String(255), index=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(50))
    seller_id = db.Column(db.Integer(), db.ForeignKey('sellers.id'))
    is_active = db.Column(db.Boolean())

    terminals = db.relationship('Terminal', secondary='terminal_group_terminal')
    terminal_group_terminal = db.relationship('TerminalGroupTerminal', back_populates='terminal_group')
