import logging
from catalog import models as m
from catalog.extensions.ram_queue_consumer.functions.utils import get_variant_attribute_value, get_default

__author__ = 'Quang.LM'

_logger = logging.getLogger(__name__)

_ATTRIBUTE_GROUP_COMMON_CODE = 'thong-tin-chung'


def _is_flat_group(attribute_group, attribute_groups):
    is_flat = attribute_group.get('is_flat')
    if is_flat == 1:
        group_attributes = filter(lambda x: x.get('is_displayed') == 1, attribute_group.get('attributes'))
        if group_attributes:
            return True
    return any(ag.get('parent_id') == attribute_group.get('id') and ag.get('is_flat') == 1 for ag in attribute_groups)


def _get_flat_common(attribute_group):
    return {
        'id': attribute_group.get('id'),
        'name': attribute_group.get('name'),
        'value': '',
        'priority': attribute_group.get('priority'),
        'parent_id': attribute_group.get('parent_id')
    }


def _get_brand(attribute_group, brand):
    if brand:
        return {
            'id': None,
            'name': 'Thương hiệu',
            'value': brand.name,
            'priority': 0,
            'parent_id': attribute_group.get('id')
        }


def _get_warranty_month(attribute_group, sellable_product):
    if sellable_product.warranty_months:
        return {
            'id': None,
            'name': 'Bảo hành',
            'value': str(sellable_product.warranty_months),
            'priority': 1,
            'parent_id': attribute_group.get('id')
        }


def _get_warranty_note(attribute_group, sellable_product):
    if sellable_product.warranty_note:
        return {
            'id': None,
            'name': 'Mô tả bảo hành',
            'value': sellable_product.warranty_note,
            'priority': 2,
            'parent_id': attribute_group.get('id')
        }


def _get_non_flat_attributes(attribute_group, variant_attributes):
    values = []
    for aga in attribute_group.get('attributes'):
        if aga.get('is_displayed') != 1:
            continue
        variant_attribute = next(filter(lambda x: x.get('attribute_id') == aga.get('attribute_id'),
                                        variant_attributes), None)
        if variant_attribute and variant_attribute.get('value') is not None:
            value = get_variant_attribute_value(variant_attribute)
            if value is None:
                continue
            values.append(f'{get_default(aga.get("text_before"))} {value} {get_default(aga.get("text_after"))}')
    return str.join('', values) if values else None


def _add_map(item, map_data):
    if item:
        key_map = ''
        for key in sorted(item.keys()):
            key_map += f'-{key}-{item[key]}-'
        if not map_data.get(key_map):
            map_data[key_map] = item


def _add_flat_or_common_groups(attribute_groups, map_groups):
    for attr_group in attribute_groups:
        if attr_group.get('code') == _ATTRIBUTE_GROUP_COMMON_CODE or _is_flat_group(attr_group, attribute_groups):
            item = _get_flat_common(attr_group)
            _add_map(item, map_groups)


class AttributeGroup:
    def __init__(self, session, sellable_product):
        self.session = session
        self.sellable_product = sellable_product

    def __add_common(self, attribute_groups, map_groups):
        sellable_product = self.sellable_product
        common_group = next(filter(lambda x: x.get('code') == _ATTRIBUTE_GROUP_COMMON_CODE, attribute_groups), None)
        if common_group:
            brand = self.session.query(m.Brand).filter(
                m.Brand.id == sellable_product.brand_id).first() if sellable_product.brand_id else None
            _add_map(_get_brand(common_group, brand), map_groups)
            _add_map(_get_warranty_month(common_group, sellable_product), map_groups)
            _add_map(_get_warranty_note(common_group, sellable_product), map_groups)

    def get_attribute_groups(self, variant_attributes, attribute_groups):
        map_groups = {}

        non_flat_groups = list(filter(lambda x: x.get('is_flat') == 0, attribute_groups))
        for attr_group in non_flat_groups:
            value = _get_non_flat_attributes(attr_group, variant_attributes)
            if value is not None:
                item = {
                    'id': attr_group.get('id'),
                    'name': attr_group.get('name'),
                    'value': value,
                    'priority': attr_group.get('priority'),
                    'parent_id': attr_group.get('parent_id'),
                }
                _add_map(item, map_groups)
        self.__add_common(attribute_groups, map_groups)
        _add_flat_or_common_groups(attribute_groups, map_groups)

        flat_groups = list(filter(lambda x: x.get('is_flat') == 1, attribute_groups))
        for attr_group in flat_groups:
            for ga in attr_group.get('attributes'):
                if ga.get('is_displayed') != 1:
                    continue
                variant_attribute = next(filter(lambda x: x.get('attribute_id') == ga.get('attribute_id'),
                                                variant_attributes), None)
                if not variant_attribute:
                    continue
                value = get_variant_attribute_value(variant_attribute)
                if value is None:
                    continue
                item = {
                    'id': None,
                    'name': ga.get('name') or '',
                    'value': value,
                    'priority': ga.get('priority'),
                    'parent_id': attr_group.get('id'),
                }
                _add_map(item, map_groups)
        response = list(map_groups.values())
        # This sort need to do like MySQL do, it order by priority first, and next is id
        # With NULL value, it should be after the valuable one like MySQL
        response.sort(key=lambda x: (x['priority'], -(x['id'] or 0)))
        return response
