# coding=utf-8
import re

from sqlalchemy import and_

from catalog import models
from catalog.models import (
    db,
    TimestampMixin
)


class ProductVariant(db.Model, TimestampMixin):
    __tablename__ = 'product_variants'

    product_id = db.Column(db.Integer, db.ForeignKey('products.id', use_alter=True))
    product = db.relationship(
        'Product',
        backref='variants',
        foreign_keys=[product_id, ]
    )
    name = db.Column(db.Text)
    code = db.Column(db.String(255))
    url_key = db.Column(db.Text)

    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

    attributes = db.relationship('Attribute', secondary='variant_attribute')

    editing_status_code = db.Column(db.String(255), db.ForeignKey('editing_status.code'),
                                    default='processing')
    editing_status = db.relationship('EditingStatus')

    all_uom_ratios = db.Column(db.String(255), default='')

    @property
    def variation_attributes(self):
        """variation_attributes
        Lấy thông tin về thuộc tính xác định biến thể
        """
        attr_ids = self.product.attribute_set.get_variation_attributes(get_all=False)
        return models.VariantAttribute.query.filter(
            models.VariantAttribute.attribute_id.in_(attr_ids),
            models.VariantAttribute.variant_id == self.id
        ).all()

    @property
    def unit(self):
        unit_attr = models.AttributeOption.query \
            .join(
            models.Attribute,
            models.Attribute.id == models.AttributeOption.attribute_id
        ) \
            .join(
            models.VariantAttribute,
            and_(
                models.VariantAttribute.attribute_id == models.Attribute.id,
                models.AttributeOption.id == models.VariantAttribute.value
            )
        ) \
            .filter(
            models.VariantAttribute.variant_id == self.id,
            models.Attribute.code == 'uom'
        ).first()

        return unit_attr

    @property
    def uom_ratio(self):
        ratio_attr = models.VariantAttribute.query \
            .join(
            models.Attribute,
            models.Attribute.id == models.VariantAttribute.attribute_id
        ) \
            .filter(
            models.VariantAttribute.variant_id == self.id,
            models.Attribute.code == 'uom_ratio'
        ).first()
        return ratio_attr.value if ratio_attr and ratio_attr.value else None

    @property
    def image(self):
        if self.images:
            return self.images[0].url
        return None

    @property
    def base_uom_id(self):
        matched = re.match(r'(\d+):1.0,', self.all_uom_ratios)
        return float(matched.group(1)) if matched else None

    def extract_uom_ids(self):
        return list(map(int, re.findall(r'(\d+):', self.all_uom_ratios)))
