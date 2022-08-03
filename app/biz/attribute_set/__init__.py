# coding=utf-8
import logging

from catalog.extensions import signals
from catalog import models as m
from catalog import celery

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@signals.on_attribute_set_created
def add_system_groups(attribute_set_id, **kwargs):
    """
    Create two default groups:
        - dimensional group contains 4 attributes: width, height, length, weight
        - uom contain 2 attributes: uom, uom_ratio

    :param attribute_set_id:
    :param kwargs:
    :return:
    """
    # dimensional group
    DIMENSIONAL_ATTRIBUTE_CODES = [
        'weight',
        'width',
        'length',
        'height',
        'pack_weight',
        'pack_width',
        'pack_length',
        'pack_height'
    ]
    priority = 1000
    dimensional_attributes = m.Attribute.query.filter(
        m.Attribute.code.in_(DIMENSIONAL_ATTRIBUTE_CODES)
    ).all()
    dim_group = m.AttributeGroup()
    dim_group.name = 'Thông tin kích thước'
    dim_group.code = 'nhom-he-thong'
    dim_group.priority = priority
    dim_group.parent_id = 0
    dim_group.level = 1
    dim_group.is_flat = 0
    dim_group.system_group = 1
    dim_group.attribute_set_id = attribute_set_id
    dim_group.path = ''
    m.db.session.add(dim_group)
    m.db.session.flush()
    dim_group.path = dim_group.id

    for index, attribute_code in enumerate(DIMENSIONAL_ATTRIBUTE_CODES):
        attribute = None
        for item in dimensional_attributes:
            if item.code == attribute_code:
                attribute = item
                break
        if attribute:
            priority += index + 1
            linked = m.AttributeGroupAttribute()
            linked.attribute_id = attribute.id
            linked.attribute_group_id = dim_group.id
            linked.priority = priority
            linked.is_displayed = 0
            linked.is_variation = 0
            m.db.session.add(linked)
            m.db.session.flush()

    # uom group
    uom_attribute = m.Attribute.query.filter(
        m.Attribute.code == 'uom'
    ).first()
    uom_ratio_attribute = m.Attribute.query.filter(
        m.Attribute.code == 'uom_ratio'
    ).first()

    priority += 1
    uom_group = m.AttributeGroup()
    uom_group.name = 'Đơn vị tính'
    uom_group.code = 'uom'
    uom_group.priority = priority
    uom_group.parent_id = 0
    uom_group.level = 1
    uom_group.is_flat = 0
    uom_group.attribute_set_id = attribute_set_id
    uom_group.system_group = 1
    uom_group.path = ''
    m.db.session.add(uom_group)
    m.db.session.flush()
    uom_group.path = uom_group.id

    priority += 1
    linked_uom_attr = m.AttributeGroupAttribute()
    linked_uom_attr.attribute_id = uom_attribute.id
    linked_uom_attr.attribute_group_id = uom_group.id
    linked_uom_attr.priority = priority
    linked_uom_attr.is_displayed = 0
    linked_uom_attr.is_variation = 1
    linked_uom_attr.variation_priority = 1
    linked_uom_attr.variation_display_type = 'text'
    m.db.session.add(linked_uom_attr)
    m.db.session.flush()

    priority += 1
    linked_uom_ratio = m.AttributeGroupAttribute()
    linked_uom_ratio.attribute_id = uom_ratio_attribute.id
    linked_uom_ratio.attribute_group_id = uom_group.id
    linked_uom_ratio.priority = priority
    linked_uom_ratio.is_displayed = 0
    linked_uom_ratio.is_variation = 1
    m.db.session.add(linked_uom_ratio)
    m.db.session.flush()

    m.db.session.commit()
