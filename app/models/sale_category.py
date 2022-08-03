# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class SaleCategory(db.Model, m.TimestampMixin):
    __tablename__ = 'sale_categories'

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'sale_categories.id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    code = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255))
    path = db.Column(db.String(255))
    depth = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    priority = db.Column(db.Integer)

    @property
    def parent(self):
        if self.parent_id:
            parent = m.SaleCategory.query.get(self.parent_id)
            return parent
        return None

    @property
    def is_leaf(self):
        n_children = m.SaleCategory.query.filter(
            m.SaleCategory.parent_id == self.id,
            m.SaleCategory.is_active,
            m.SaleCategory.path.like(f'{self.path}/%')
        ).count()
        return n_children == 0

    def get_children(self, **kwargs):
        kwargs.update({
            'parent_id': self.id,
            'is_active': True,
        })
        return m.SaleCategory.query.filter_by(**kwargs)

    @property
    def children(self):
        return self.get_children()
