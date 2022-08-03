from catalog.constants import OPTION_VALUE_NOT_DISPLAY, PACK_CODE_ATTRIBUTES
from catalog.utils import safe_cast
from catalog import models as m
from sqlalchemy.orm import load_only
from catalog.extensions.ram_queue_consumer.functions.attribute_group import AttributeGroup
from catalog.extensions.ram_queue_consumer.functions.product_group import ProductGroup
from catalog.extensions.ram_queue_consumer.functions.seo_config import SeoConfig


def _get_unit_code(map_units, unit_id):
    if not unit_id:
        return ''
    unit = map_units.get(unit_id)
    if unit:
        return unit.code
    return ''


def _add_map(map_data, value, key, list_field=None):
    if list_field:
        values = map_data.get(key, {}).get(list_field)
    else:
        values = map_data.get(key)
    if not values:
        values = []
    values.append(value)
    if list_field:
        map_data[key][list_field] = values
    else:
        map_data[key] = values


def _get_attribute_options(map_all_options, attr_id, value, value_type):
    display_options = []
    if value_type not in ('text', 'number'):
        attribute_options = map_all_options.get(attr_id) or []
        option_ids = list(map(lambda x: safe_cast(x, int), value.split(',')))
        for option_id in option_ids:
            for option in attribute_options:
                if option.get('id') == option_id:
                    display_options.append(option)
                    break
    return display_options


def _set_pack_attribute_value(attribute, map_attribute_values):
    attribute_code = attribute.get('code').replace('pack_', '')
    for k, v in map_attribute_values.items():
        attribute = v.get('attribute')
        if attribute and attribute.get('code') == attribute_code:
            return v.get('value')


def _get_attributes(map_attribute_values, attribute_groups):
    attributes = []
    for ag in attribute_groups:
        for attr in ag.get('attributes'):
            value = map_attribute_values.get(attr.get('attribute_id')) or {}
            attribute = value.get('attribute') or {}
            if attribute.get('value_type') in ('text', 'number'):
                values = [{
                    'option_id': None,
                    'value': value.get('value')
                }]
            else:
                options = attribute.get('options') or []
                values = list(map(lambda x: {
                    'option_id': x.get('id'),
                    'value': x.get('value')
                }, options))
            if attr.get('code') in PACK_CODE_ATTRIBUTES and not values:
                values.append({
                    'option_id': None,
                    'value': _set_pack_attribute_value(attr, map_attribute_values)
                })
            attributes.append({
                'id': attr.get('attribute_id'),
                'code': attr.get('code'),
                'name': attr.get('name'),
                'priority': attr.get('priority'),
                'is_comparable': attr.get('is_comparable'),
                'is_filterable': attr.get('is_filterable'),
                'is_searchable': attr.get('is_searchable'),
                'values': values
            })
    return attributes


def _get_manufacture(variant_attributes):
    for va in variant_attributes:
        attribute = va.get('attribute') or {}
        if attribute.get('code') == m.MANUFACTURE_CODE:
            options = attribute.get('options') or []
            for o in options:
                return {
                    'id': o.get('id'),
                    'code': o.get('code') or str(o.get('id')),
                    'name': o.get('value')
                }


class AdvancedInfo:

    def __init__(self, session):
        self.session = session

    def __map_units(self, options):
        unit_ids = list(map(lambda x: x.unit_id, filter(lambda x: x.unit_id and x.unit_id > 0, options)))
        units = self.session.query(m.ProductUnit).filter(m.ProductUnit.id.in_(unit_ids))
        map_units = {}
        for u in units:
            map_units[u.id] = u
        return map_units

    def __map_options_attributes(self, attr_ids):
        options = self.session.query(m.AttributeOption).filter(
            m.AttributeOption.attribute_id.in_(attr_ids),
            m.AttributeOption.value != OPTION_VALUE_NOT_DISPLAY
        ).all()
        map_units = self.__map_units(options)
        map_options = {}
        for o in options:
            item = {
                'id': o.id,
                'value': o.value,
                'thumbnail_url': o.thumbnail_url,
                'attribute_id': o.attribute_id,
                'unit_id': o.unit_id,
                'unit_code': _get_unit_code(map_units, o.unit_id),
                'priority': o.priority
            }
            _add_map(map_options, item, o.attribute_id)
        return map_options

    def __get_all_variant_attributes(self, sellable_product, map_variations, map_all_options):
        groups = self.session.query(
            m.VariantAttribute.id,
            m.VariantAttribute.variant_id,
            m.VariantAttribute.attribute_id,
            m.VariantAttribute.value,
            m.Attribute.value_type,
            m.Attribute.code
        ).join(m.ProductVariant, m.ProductVariant.id == m.VariantAttribute.variant_id).join(
            m.Attribute,
            m.Attribute.id == m.VariantAttribute.attribute_id
        ).filter(
            m.ProductVariant.product_id == sellable_product.product_id,
            m.VariantAttribute.value != OPTION_VALUE_NOT_DISPLAY
        ).all()
        all_variant_attributes = []
        variant_attributes = []
        map_attribute_values = {}
        for var_attr_id, variant_id, attr_id, value, value_type, attr_code in groups:
            display_options = _get_attribute_options(map_all_options, attr_id, value, value_type)
            item = {
                'id': var_attr_id,
                'variant_id': variant_id,
                'attribute_id': attr_id,
                'value': value,
                'attribute': {
                    'id': attr_id,
                    'code': attr_code,
                    'value_type': value_type,
                    'options': display_options
                }
            }
            if map_variations.get(attr_id):
                all_variant_attributes.append(item)
            if variant_id == sellable_product.variant_id:
                variant_attributes.append(item)
                map_attribute_values[attr_id] = {
                    'id': var_attr_id,
                    'variant_id': variant_id,
                    'attribute_id': attr_id,
                    'value': value,
                    'attribute': {
                        'id': attr_id,
                        'code': attr_code,
                        'value_type': value_type,
                        'options': display_options
                    }
                }
        return all_variant_attributes, variant_attributes, map_attribute_values

    def __get_attribute_group_attributes(self, sellable_product):
        return self.session.query(
            m.AttributeGroup,
            m.AttributeGroupAttribute,
            m.Attribute
        ).join(
            m.AttributeGroupAttribute,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id, isouter=True
        ).join(
            m.Attribute,
            m.Attribute.id == m.AttributeGroupAttribute.attribute_id, isouter=True
        ).filter(
            m.AttributeGroup.attribute_set_id == sellable_product.attribute_set_id
        ).order_by(m.AttributeGroup.priority, m.AttributeGroupAttribute.priority).all()

    def __get_attribute_groups(self, sellable_product):
        groups = self.__get_attribute_group_attributes(sellable_product)
        attr_ids = []
        for _, _, attr in groups:
            if attr:
                attr_ids.append(attr.id)
        map_all_options = self.__map_options_attributes(attr_ids)
        map_groups = {}
        map_variations = {}
        for group, attr_group, attr in groups:
            item_group = {
                'id': group.id,
                'code': group.code,
                'name': group.name,
                'is_flat': group.is_flat,
                'priority': group.priority,
                'parent_id': group.parent_id,
                'attributes': []
            }
            if not map_groups.get(group.id):
                map_groups[group.id] = item_group
            if not attr or not attr_group:
                continue
            item_attr = {
                'attribute_id': attr.id,
                'code': attr.code,
                'name': attr.display_name or attr.name,
                'value_type': attr.value_type,
                'is_searchable': attr.is_searchable,
                'is_filterable': attr.is_filterable,
                'is_comparable': attr.is_comparable,
                'text_before': attr_group.text_before,
                'text_after': attr_group.text_after,
                'is_variation': attr_group.is_variation,
                'priority': attr_group.priority,
                'variation_display_type': attr_group.variation_display_type,
                'is_displayed': attr_group.is_displayed,
                'options': map_all_options.get(attr.id)
            }
            _add_map(map_groups, item_attr, group.id, 'attributes')
            map_variations[attr.id] = attr_group.is_variation
        return list(map_groups.values()), map_variations, map_all_options

    def __get_product(self, sellable_product):
        return self.session.query(m.Product).filter(
            m.Product.id == sellable_product.product_id
        ).options(load_only('id', 'name')).first()

    def get_advanced_info(self, sellable_product):
        attribute_groups, map_variations, map_all_options = self.__get_attribute_groups(sellable_product)
        all_variant_attributes, variant_attributes, map_attribute_values = self.__get_all_variant_attributes(
            sellable_product, map_variations, map_all_options)
        attr_group_obj = AttributeGroup(self.session, sellable_product)
        product_group_obj = ProductGroup(self.session, sellable_product, all_variant_attributes)
        seo_config_obj = SeoConfig(self.session, sellable_product)
        default_seo = seo_config_obj.get_seo_default(variant_attributes)
        config_seo = seo_config_obj.get_seo_by_config(variant_attributes)
        variants = product_group_obj.get_variants()
        configurations = product_group_obj.get_configurations(attribute_groups)
        product = self.__get_product(sellable_product)
        return {
            'manufacture': _get_manufacture(variant_attributes),
            'attributes': _get_attributes(map_attribute_values, attribute_groups),
            'default_seo': default_seo,
            'config_seo': config_seo,
            'product_group': {
                'id': product.id,
                'name': product.name,
                'visible': 'individual',
                'configurations': configurations or None,
                'variants': variants or None
            },
            'attribute_groups': attr_group_obj.get_attribute_groups(variant_attributes, attribute_groups)
        }
