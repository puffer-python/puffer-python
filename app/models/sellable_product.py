# coding=utf-8

import logging
from sqlalchemy.orm import backref, aliased
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import text
from catalog.models import (
    db,
    TimestampMixin
)
from catalog import models as m

_logger = logging.getLogger(__name__)


class SellableProduct(db.Model, TimestampMixin):
    __tablename__ = 'sellable_products'

    name = db.Column(db.String(255), nullable=False, unique=False)
    sku = db.Column(db.String(100), nullable=False, unique=True, index=True)
    seller_sku = db.Column(db.String(100), index=True)
    barcode = db.Column(db.String(50))
    warranty_months = db.Column(db.Integer, default=0, nullable=False)
    need_convert_qty = db.Column(db.Integer, default=0, nullable=False)
    warranty_note = db.Column(db.String(255))
    label = db.Column(db.String(255))
    is_bundle = db.Column(db.Boolean(), default=False, nullable=False)
    status = db.Column(db.String(255))  # TODO: move to editing_status_code
    supplier_sale_price = db.Column(db.Integer)
    sale_price = db.Column(db.Integer)
    model = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
    allow_selling_without_stock = db.Column(db.Boolean(), default=False, nullable=True)
    manage_serial = db.Column(db.Boolean)
    tracking_type = db.Column(db.Boolean)
    auto_generate_serial = db.Column(db.Boolean)
    part_number = db.Column(db.String(255))
    comment = db.Column(db.String(255))
    product_type = db.Column(db.String(255))
    expiry_tracking = db.Column(db.Boolean)
    expiration_type = db.Column(db.Integer)
    days_before_exp_lock = db.Column(db.Integer)
    objective = db.Column(db.String(255))
    uom_code = db.Column(db.String(255))
    uom_ratio = db.Column(db.Float())
    uom_name = db.Column(db.String(255))

    tax_in_code = db.Column(db.String(10), db.ForeignKey('taxes.code'))
    tax_in = db.relationship(
        'Tax',
        primaryjoin='SellableProduct.tax_in_code == Tax.code'
    )

    tax_out_code = db.Column(db.String(10), db.ForeignKey('taxes.code'))
    tax_out = db.relationship(
        'Tax',
        primaryjoin='SellableProduct.tax_out_code == Tax.code'
    )

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey('brands.id')
    )
    brand = db.relationship('Brand')

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id')
    )
    category = db.relationship('Category')

    master_category_id = db.Column(
        db.Integer,
        db.ForeignKey('master_categories.id')
    )
    master_category = db.relationship('MasterCategory')

    attribute_set_id = db.Column(
        db.Integer,
        db.ForeignKey('attribute_sets.id')
    )
    attribute_set = db.relationship('AttributeSet')

    unit_id = db.Column(
        db.Integer,
        db.ForeignKey('units.id')
    )
    unit = db.relationship('Unit', foreign_keys=[unit_id, ])

    unit_po_id = db.Column(
        db.Integer,
        db.ForeignKey('units.id')
    )
    unit_po = db.relationship('Unit', foreign_keys=[unit_po_id, ])

    color_id = db.Column(
        db.Integer,
        db.ForeignKey('colors.id')
    )
    color = db.relationship('Color', foreign_keys=[color_id, ])

    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('product_variants.id'),
        nullable=False
    )
    product_variant = db.relationship(
        'ProductVariant',
        backref='sellable_products'
    )  # type: m.ProductVariant

    editing_status_code = db.Column(
        db.String(20),
        db.ForeignKey('editing_status.code'),
        nullable=False,
        default='draft'
    )
    editing_status = db.relationship('EditingStatus')

    selling_status_code = db.Column(
        db.String(20),
        db.ForeignKey('selling_status.code')
    )
    selling_status = db.relationship('SellingStatus')

    children = db.relationship(  # bundle item
        'SellableProduct',
        secondary='sellable_product_bundles',
        primaryjoin='SellableProduct.id == SellableProductBundle.bundle_id',
        secondaryjoin='SellableProduct.id == SellableProductBundle.sellable_product_id',
        backref=backref('parents')
    )

    bundles = db.relationship(
        'SellableProductBundle',
        secondary='sellable_product_bundles',
        primaryjoin='SellableProduct.id == SellableProductBundle.bundle_id',
        secondaryjoin='SellableProduct.id == SellableProductBundle.sellable_product_id',
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey('sellers.id'),
        nullable=False
    )
    seller = db.relationship(
        'Seller',
        backref='sellable_products',
    )

    provider_id = db.Column(
        db.Integer,
        db.ForeignKey('providers.id')
    )
    provider = db.relationship(
        'Provider',
        backref='sellable_products'
    )

    terminals = db.relationship(
        'Terminal',
        secondary='sellable_product_terminal'
    )

    terminal_seo = db.relationship(
        'SellableProductSeoInfoTerminal',
        primaryjoin='SellableProduct.id == SellableProductSeoInfoTerminal.sellable_product_id and SellableProductSeoInfoTerminal.code == 0',
        uselist=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'products.id'
        )
    )
    product = db.relationship('Product', backref='sellable_products')

    price = db.relationship(
        'SellableProductPrice',
        backref='sellable_products'
    )

    ext_brand_data = None
    ext_editing_status_data = None
    ext_attribute_set_data = None
    ext_category_data = None
    ext_master_category_data = None
    ext_product_variant_data = None
    ext_product_data = None
    ext_barcodes_data = None
    ext_variant_images_data = None
    ext_shipping_type_data = None
    loaded_barcodes = None
    is_sub = False
    sub_id = None
    sub_sku = None

    @property
    def response_id(self):
        if self.is_sub:
            return self.sub_id
        return self.id

    @property
    def response_sku(self):
        if self.is_sub:
            return self.sub_sku
        return self.sku

    @property
    def response_seller_sku(self):
        if self.is_sub:
            return self.sub_sku
        return self.seller_sku

    @property
    def shipping_type_code(self):
        return [shipping_type.code for shipping_type in self.shipping_types]

    @property
    def shipping_type_id(self):
        return None if not self.shipping_types else self.shipping_types[0].id

    shipping_types = db.relationship(
        'ShippingType',
        secondary='sellable_product_shipping_type'
    )

    def __get_barcodes(self):
        if not self.loaded_barcodes and not self.ext_barcodes_data:
            self.ext_barcodes_data = m.SellableProductBarcode.query.filter(
                m.SellableProductBarcode.sellable_product_id == self.id
            ).order_by(m.SellableProductBarcode.id).all() or []

    @property
    def barcodes(self):
        self.__get_barcodes()
        if self.ext_barcodes_data:
            return list(map(lambda x: x.barcode, self.ext_barcodes_data))
        if self.barcode:
            return self.barcode.split(',')
        return []

    @property
    def barcodes_with_source(self):
        self.__get_barcodes()
        if self.ext_barcodes_data:
            return list(map(lambda x: {'barcode': x.barcode, 'source': x.source, 'is_default': x.is_default},
                            self.ext_barcodes_data))
        if self.barcode:
            _barcodes = self.barcode.split(',')
            _len = len(_barcodes)
            res = []
            for i in range(_len):
                is_default = True if i == _len - 1 else False
                res.append({
                    'barcode': _barcodes[i], 'source': '', 'is_default': is_default
                })
            return res
        return []

    __seller_category_code = None

    @property
    def seller_category_code(self):
        if self.__seller_category_code:
            return self.__seller_category_code

        self.set_seller_category_code(m.db.session)
        return self.__seller_category_code

    def set_seller_category_code(self, session):
        from catalog.services.seller import get_default_platform_owner_of_seller
        owner_seller_id = get_default_platform_owner_of_seller(self.seller_id, session)
        self.__seller_category_code = ''
        if owner_seller_id:
            sql = """
            SELECT c.code FROM categories c
            JOIN product_categories pc ON c.id = pc.category_id
            WHERE c.seller_id = :seller_id AND pc.product_id = :product_id
            """
            results = session.execute(text(sql), {
                'seller_id': owner_seller_id,
                'product_id': self.product_id
            })
            for r in results:
                self.__seller_category_code = r['code']

    @hybrid_property
    def uom_po_code(self):
        return self.uom_code

    @hybrid_property
    def attributes(self):
        attrs = dict()
        # initial with variant attributes
        for attr in self.product_variant.variant_attributes:
            attrs[attr.id] = attr

        # update with product attributes
        for attr in self.product_variant.product.product_attributes:
            if attr.id not in attrs:
                attrs[attr.id] = attr
        return attrs.values()

    @hybrid_property
    def product_type_obj(self):
        type_obj = m.Misc.query.filter(
            m.Misc.code == self.product_type,
            m.Misc.type == 'product_type'
        ).first()  # type: m.Misc
        return type_obj

    @hybrid_property
    def is_active(self):
        return self.editing_status_code != 'inactive'

    @hybrid_property
    def avatar_url(self):
        image = m.VariantImage.query.filter(
            m.VariantImage.product_variant_id == self.variant_id
        ).order_by(m.VariantImage.priority).first()  # type: m.VariantImage
        if image is not None:
            return image.url
        return 'https://lh3.googleusercontent.com/3_NmlckZlR8z19m8L0JQ2wOoz1t-ms07tr7LyVCmha6lFogTWA_cRFyf5Zl9KOR47s45tATXDNv_2pZ7elc'

    def get_expiration_type(self):
        if self.expiration_type == 1:
            return 'Ngày'
        elif self.expiration_type == 2:
            return 'Tháng'
        return None

    @hybrid_property
    def line_category(self):
        owner_category = aliased(m.PlatformSellers)
        seller_platform_default = m.PlatformSellers.query.join(
            owner_category,
            owner_category.platform_id == m.PlatformSellers.platform_id and owner_category.is_default.is_(True)
        ).filter(
            m.PlatformSellers.is_owner.is_(True),
            owner_category.seller_id == self.seller_id
        ).first()
        seller_id = seller_platform_default.seller_id if seller_platform_default else self.seller_id
        return m.Category.query.join(m.ProductCategory).filter(
            m.Category.seller_id == seller_id,
            m.ProductCategory.product_id == self.product_id
        ).first()

    def get_attributes_by_codes(self, codes):
        variant_attributes = m.VariantAttribute.query.join(
            m.Attribute,
            m.Attribute.id == m.VariantAttribute.attribute_id
        ).filter(
            m.VariantAttribute.variant_id == self.variant_id,
            m.Attribute.code.in_(codes)
        ).all()
        return variant_attributes
