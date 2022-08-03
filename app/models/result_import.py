# coding=utf-8
import sqlalchemy as sa
from catalog import models as m
from catalog.models import db, TimestampMixin


class ResultImport(db.Model, TimestampMixin):
    __tablename__ = 'result_imports'

    import_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey('file_imports.id')
    )
    data = sa.Column(sa.JSON())
    output = sa.Column(sa.JSON())
    status = sa.Column(sa.String(30), comment='success|failure|fatal')
    message = sa.Column(sa.String(255))
    tag = sa.Column(sa.String(32))
    product_id = sa.Column(sa.Integer())
    updated_by = sa.Column(sa.String(100))
