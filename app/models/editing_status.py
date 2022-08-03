# coding=utf-8


from catalog.models import db


class EditingStatus(db.Model):
    __tablename__ = 'editing_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    code = db.Column(db.String(255), nullable=False, index=True)
    config = db.Column(db.Text)
    can_moved_status = db.Column(db.String(255))
