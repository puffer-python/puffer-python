# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class MasterCategory(db.Model, m.TimestampMixin):
    __tablename__ = 'master_categories'

    code = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    name_ascii = db.Column(db.String(255))
    image = db.Column(db.String(255))
    path = db.Column(db.String(255))
    depth = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    manage_serial = db.Column(db.Boolean)
    auto_generate_serial = db.Column(db.Boolean())

    attribute_set_id = db.Column(db.Integer, db.ForeignKey('attribute_sets.id'))
    attribute_set = db.relationship('AttributeSet')

    tax_in_code = db.Column(db.String(10))
    tax_in = db.relationship('Tax',
                             foreign_keys=[tax_in_code, ],
                             primaryjoin='MasterCategory.tax_in_code == Tax.code')
    tax_out_code = db.Column(db.String(10))
    tax_out = db.relationship('Tax',
                              foreign_keys=[tax_out_code, ],
                              primaryjoin='MasterCategory.tax_out_code == Tax.code')

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'master_categories.id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    parent = db.relationship('MasterCategory',
                             remote_side='MasterCategory.id',
                             backref='children')

    @property
    def root(self):
        root_id = self.path.split('/')[0]
        if str(self.id) == root_id:
            return None
        return m.MasterCategory.query.get(int(root_id))

    @property
    def is_leaf(self):
        n_children = m.MasterCategory.query.filter(
            m.MasterCategory.parent_id == self.id,
            m.MasterCategory.is_active,
            m.MasterCategory.path.like(f'{self.path}/%')
        ).count()
        return n_children == 0

    @property
    def full_path(self):
        path = ''
        cats = m.MasterCategory.query.filter(
            m.MasterCategory.id.in_(self.path.split('/'))
        ).order_by('depth')
        for cat in cats:
            path = f'{path} / {cat.name}' if path else cat.name
        return path

    ext_full_path_data = None
