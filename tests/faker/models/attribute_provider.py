# coding=utf-8
import logging
import random
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class AttributeProvider(faker.providers.BaseProvider):
    def attribute_option(self, attribute_id, value=None, code=None, seller_id=None, thumbnail_url=None, priority=None):
        option = m.AttributeOption()
        option.value = value or fake.text()
        option.attribute_id = attribute_id
        option.code = code or fake.unique_str()
        option.seller_id = seller_id if seller_id is not None else fake.seller().id
        option.priority = priority or fake.integer()
        if attribute_id % 2:
            unit = fake.attribute_unit()
            option.unit_id = unit.id
        option.thumbnail_url = thumbnail_url
        m.db.session.add(option)
        m.db.session.flush()
        return option

    def attribute(self, variant_id=None, value_type=None, group_ids=None,
                  is_required=None, unit_id=None, code=None, suffix=None,
                  is_none_unit_id=False, is_variation=False, is_unsigned=None, **kwargs):
        attribute = m.Attribute()
        attribute.name = fake.text()
        attribute.code = code or fake.unique_str()
        attribute.value_type = value_type or self.attribute_value_type()
        attribute.description = fake.text()
        attribute.display_name = fake.text()
        attribute.is_required = random.choice([0, 1]) if is_required is None else is_required
        attribute.is_comparable = random.choice([0, 1])
        attribute.is_searchable = random.choice([0, 1])
        attribute.is_filterable = random.choice([0, 1])
        attribute.suffix = suffix
        attribute.is_system = random.choice((True, False))
        if is_none_unit_id:
            attribute.unit_id = None
        else:
            attribute.unit_id = unit_id if unit_id is not None else fake.attribute_unit().id
        attribute.is_variation = 0
        attribute.is_unsigned = is_unsigned

        m.db.session.add(attribute)
        m.db.session.flush()

        if variant_id:
            variant_attr = self.variant_attribute(
                variant_id=variant_id,
                attribute_id=attribute.id
            )
            if attribute.value_type == 'number':
                variant_attr.value = fake.integer()
            elif attribute.value_type == 'selection':
                opt = self.attribute_option(attribute.id)
                variant_attr.value = opt.id
            elif attribute.value_type == 'multiple_select':
                opt_ids = [opt.id for opt in
                           [self.attribute_option(attribute.id)
                            for _ in range(0, 3)]]
                variant_attr.value = ','.join(str(opt) for opt in opt_ids)
        else:
            if attribute.value_type == 'selection':
                self.attribute_option(attribute.id)
            elif attribute.value_type == 'multiple_select':
                [self.attribute_option(attribute.id) for _ in range(0, 3)]

        if group_ids:
            self.attribute_group_attribute(
                attribute_id=attribute.id,
                group_ids=group_ids,
                is_variation=is_variation
            )
        m.db.session.flush()

        return attribute

    def uom_attribute(self, attribute_set_id):
        existed = m.Attribute.query.filter(
            m.Attribute.code == 'uom'
        ).first()
        if existed:
            return existed

        uom_attr_gr = fake.attribute_group(set_id=attribute_set_id, system_group=1, code='uom')
        uom_attr = self.attribute(code='uom', value_type='selection', group_ids=[uom_attr_gr.id], is_variation=True)

        [fake.attribute_option(attribute_id=uom_attr.id) for _ in range(10)]

        return uom_attr

    def uom_ratio_attribute(self, attribute_set_id, ratio_value=None):
        existed = m.Attribute.query.filter(
            m.Attribute.code == 'uom_ratio'
        ).first()
        if existed:
            return existed

        uom_ratio_attr_gr = fake.attribute_group(set_id=attribute_set_id, system_group=1, code='uom_ratio')
        uom_ratio_attr = self.attribute(code='uom_ratio', value_type='number', group_ids=[uom_ratio_attr_gr.id],
                                        is_variation=True)

        return uom_ratio_attr

    def attribute_value_type(self):
        return random.choice([
            'text',
            'number',
            'selection',
            'multiple_select'
        ])

    def variant_attribute(self, variant_id, attribute_id, option_id=None, value=None):
        """

        :param variant_id:
        :param attribute_id:
        :param option_id:
        :param value:
        :return:
        """
        variant_attribute = m.VariantAttribute()
        variant_attribute.value = option_id or value or fake.text()
        variant_attribute.variant_id = variant_id
        variant_attribute.attribute_id = attribute_id

        m.db.session.add(variant_attribute)
        m.db.session.flush()

        return variant_attribute

    def attribute_group_attribute(self, attribute_id, group_ids,
                                  is_variation=0):
        """

        :param attribute_id:
        :param group_ids:
        :param is_variation:
        :return:
        """
        attr_gr_attr = m.AttributeGroupAttribute()
        attr_gr_attr.priority = fake.integer()
        attr_gr_attr.attribute_id = attribute_id
        attr_gr_attr.attribute_group_id = random.choice(group_ids)
        attr_gr_attr.is_variation = is_variation
        attr_gr_attr.variation_priority = random.choice([0, 1])
        m.db.session.add(attr_gr_attr)
        m.db.session.flush()
        return attr_gr_attr
