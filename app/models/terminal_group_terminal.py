from catalog.models import db
from catalog.models import TimestampMixin


class TerminalGroupTerminal(db.Model, TimestampMixin):
    __tablename__ = 'terminal_group_terminal'

    terminal_code = db.Column(db.String(255), db.ForeignKey('terminals.code'))
    terminal_group_code = db.Column(db.String(255), db.ForeignKey('terminal_groups.code'))

    terminal_group = db.relationship(
        "TerminalGroup",
        back_populates='terminal_group_terminal'
    )
