# coding=utf-8

from catalog import utils
from sqlalchemy.ext.hybrid import hybrid_property

from catalog.models import (
    db,
    Misc,
    TimestampMixin
)


class Product(db.Model, TimestampMixin):
    __tablename__ = 'products'

    name = db.Column(db.Text(), nullable=False)
    is_bundle = db.Column(db.Boolean())
    display_name = db.Column(db.Text())
    short_name = db.Column(db.Text())
    model = db.Column(db.String(255))
    type = db.Column(db.String(30))
    is_physical = db.Column(db.Boolean)
    url_key = db.Column(db.String(500))
    spu = db.Column(db.String(10), unique=True)
    description = db.Column(db.Text())
    detailed_description = db.Column(db.Text())
    provider_id = db.Column(db.Integer())
    warranty_months = db.Column(db.Integer())
    warranty_note = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
    meta_title = db.Column(db.Text)
    meta_description = db.Column(db.Text)
    meta_keyword = db.Column(db.Text)

    attribute_set_id = db.Column(db.Integer, db.ForeignKey('attribute_sets.id'))
    attribute_set = db.relationship('AttributeSet', backref='products')

    category_id = db.Column(
        db.ForeignKey('categories.id')
    )
    category = db.relationship('Category', backref='products')

    master_category_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'master_categories.id',
            name='FK_products__master_category_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    master_category = db.relationship(
        'MasterCategory',
        backref='products',
    )  # type: m.MasterCategory

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'brands.id',
            name='FK_products__brand_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=False
    )
    brand = db.relationship(
        'Brand',
        backref='products',
    )  # type: Brand

    tax_in_code = db.Column(db.String(10), db.ForeignKey('taxes.code'))
    tax_in = db.relationship('Tax', primaryjoin='Product.tax_in_code == Tax.code')

    tax_out_code = db.Column(db.String(10), db.ForeignKey('taxes.code'))
    tax_out = db.relationship('Tax', primaryjoin='Product.tax_out_code == Tax.code')

    unit_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'units.id',
            name='FK_products_unit_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=True
    )
    unit = db.relationship(
        'Unit',
        primaryjoin='Product.unit_id == Unit.id',
        foreign_keys=[unit_id, ]
    )

    unit_po_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'units.id',
            name='FK_products_unit_po_id',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
        nullable=True
    )
    unit_po = db.relationship(
        'Unit',
        primaryjoin='Product.unit_po_id == Unit.id',
        foreign_keys=[unit_po_id, ]
    )

    product_status_history = db.relationship(
        'EditingStatusHistory',
        order_by='desc(EditingStatusHistory.id)'
    )

    editing_status_code = db.Column(db.String(30), db.ForeignKey('editing_status.code'),
                                    nullable=False, default='draft')
    editing_status = db.relationship('EditingStatus')

    default_variant_id = db.Column(db.Integer,
                                   db.ForeignKey('product_variants.id'))
    default_variant = db.relationship('ProductVariant',
                                      primaryjoin='Product.default_variant_id == ProductVariant.id',
                                      uselist=False,
                                      post_update=True)

    @hybrid_property
    def type_name(self):
        type_obj = Misc.query.filter(
            Misc.code == self.type,
            Misc.type == 'product_type'
        ).first()  # type: Misc

        if type_obj:
            return type_obj.name
