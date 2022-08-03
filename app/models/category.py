# coding=utf-8
import logging

from catalog import models as m
from catalog.models import db

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Category(db.Model, m.TimestampMixin):
    """
    Quản lý categories
    """
    __tablename__ = 'categories'

    code = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255))
    eng_name = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_adult = db.Column(db.Boolean, default=False, nullable=False)
    depth = db.Column(db.Integer)
    tax_in_code = db.Column(db.String(10))
    tax_out_code = db.Column(db.String(10))
    manage_serial = db.Column(db.Boolean, nullable=False, default=False)
    auto_generate_serial = db.Column(db.Boolean())
    unit_id = db.Column(db.Integer)
    attribute_set_id = db.Column(
        db.Integer,
        db.ForeignKey('attribute_sets.id'),
        nullable=True,
        index=True
    )
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'))
    seller = db.relationship('Seller', backref='categories')
    master_category_id = db.Column(db.Integer, db.ForeignKey('master_categories.id'))

    master_category = db.relationship(
        'MasterCategory',
        foreign_keys=[master_category_id, ],
        primaryjoin='Category.master_category_id == MasterCategory.id')

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'categories.id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    parent = db.relationship('Category', remote_side='Category.id', backref='children')

    attribute_set = db.relationship('AttributeSet')

    tax_in = db.relationship('Tax',
                             foreign_keys=[tax_in_code, ],
                             primaryjoin='Category.tax_in_code == Tax.code')
    tax_out = db.relationship('Tax',
                              foreign_keys=[tax_out_code, ],
                              primaryjoin='Category.tax_out_code == Tax.code')

    shipping_types = db.relationship(
        'ShippingType',
        secondary='category_shipping_type'
    )

    mapping_shipping_types = None

    db.Index('category_index_seller_id_depth', seller_id, depth)

    @property
    def root(self):
        root_id = self.path.split('/')[0]
        if str(self.id) == root_id:
            return None
        return m.Category.query.get(int(root_id))

    def get_children(self, filters):
        query = m.Category.query.filter(
            m.Category.parent_id == self.id
        )
        is_active = filters.get('is_active')
        if is_active is not None:
            query = query.filter(
                m.Category.is_active.is_(is_active)
            )

        return query.all()

    @property
    def is_leaf(self):
        n_children = m.Category.query.filter(
            m.Category.parent_id == self.id,
            m.Category.is_active,
            m.Category.path.like(f'{self.path}/%')
        ).count()
        return n_children == 0

    @property
    def full_path(self):
        path = ''
        cats = m.Category.query.filter(
            m.Category.id.in_(self.path.split('/'))
        ).order_by('depth')
        for cat in cats:
            path = f'{path} / {cat.name}' if path else cat.name
        return path

    ext_full_path_data = None

    @property
    def default_attribute_set(self):
        if self.attribute_set:
            return self.attribute_set
        default_category = m.Category.query.filter(
            m.Category.id.in_(self.path.split('/')),
            m.Category.attribute_set_id > 0
        ).order_by(m.Category.depth.desc()).first()
        if default_category:
            return default_category.attribute_set
        return None
