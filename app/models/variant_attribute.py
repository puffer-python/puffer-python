# coding=utf-8

from catalog.models.attribute_option import AttributeOption
from catalog.utils import safe_cast
from sqlalchemy.orm import backref
from catalog.models import (
    db,
    TimestampMixin,
    Attribute,
)
from catalog.constants import ATTRIBUTE_TYPE


class VariantAttribute(db.Model, TimestampMixin):
    __tablename__ = 'variant_attribute'

    value = db.Column(db.Text, nullable=False)

    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'),
                           nullable=False)
    product_variant = db.relationship('ProductVariant', backref=backref('variant_attributes'))

    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'),
                             nullable=False)
    attribute = db.relationship('Attribute', backref=backref('variant_attributes'))

    unit_id = db.Column(db.Integer)

    def get_option_value(self):
        option_id = safe_cast(self.value, int)
        if not option_id:
            return ''
        option = AttributeOption.query.filter(AttributeOption.attribute_id == self.attribute_id,
                                              AttributeOption.id == option_id).first()
        if not option:
            return ''
        return option.value

    def get_value(self):
        """attribute_value
        :return: Union[str, int, float, models.AttributeOption, list[models.AttributeOption]]
        """
        if self.attribute.value_type == 'text':
            return self.value
        if self.attribute.value_type == 'number':
            try:
                return int(self.value)
            except:
                return float(self.value)

        options_filter = filter(
            lambda option: str(option.id) in str(self.value).split(','),
            self.attribute.options
        )
        options = list(options_filter)
        if self.attribute.value_type == 'selection':
            return options[0] if len(options) > 0 else None
        return options

    def set_value(self, raw_value):
        attribute = Attribute.query.get(self.attribute_id)
        if attribute is None:
            raise ValueError('Thuộc tính không tồn tại')
        if attribute.value_type == 'multiple_select':
            self.value = ','.join(map(str, raw_value))
        else:
            if attribute.code in ('width', 'length', 'height', 'weight'):
                self.value = round(float(raw_value), 2)
            else:
                self.value = raw_value

    @property
    def attribute_option(self):
        option_id = safe_cast(self.value, int)
        if not option_id:
            return ''
        return AttributeOption.query.get(option_id)
    
    @property
    def attribute_option_value(self):
        option_id = safe_cast(self.value, int)
        if self.attribute.value_type in [ATTRIBUTE_TYPE.SELECTION, ATTRIBUTE_TYPE.MULTIPLE_SELECT]:
            attribute_option = AttributeOption.query.get(option_id)
            return attribute_option.value
        return self.value
