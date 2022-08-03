# coding=utf-8
import logging
from sqlalchemy.orm import load_only

from catalog import app
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@app.cli.command()
def populate_uom_data():
    """
    Populate UOM attributes and attribute groups data. Move dimensional group
    to all attribute sets.

    :return:
    """
    # create uom variant attributes
    uom_attr = m.Attribute()
    uom_attr.name = 'Đơn vị tính'
    uom_attr.code = 'uom'
    uom_attr.value_type = 'selection'
    m.db.session.add(uom_attr)
    m.db.session.flush()

    ratio_attr = m.Attribute()
    ratio_attr.name = 'Tỉ lệ quy đổi'
    ratio_attr.code = 'uom_ratio'
    ratio_attr.value_type = 'text'
    m.db.session.add(ratio_attr)
    m.db.session.flush()

    # migrate unit values to attribute option
    units = m.Unit.query.all()
    for unit in units:
        option = m.AttributeOption()
        option.value = unit.name
        option.code = unit.code
        option.attribute_id = uom_attr.id
        m.db.session.add(option)
    m.db.session.flush()

    # remove old dimensional system group
    query = m.AttributeGroup.query.filter(
        m.AttributeGroup.system_group == 1
    )
    old_dim_group = query.first()
    dim_attr_ids = [each[0] for each in m.db.session.query(
        m.AttributeGroupAttribute.attribute_id).filter(
        m.AttributeGroupAttribute.attribute_group_id == old_dim_group.id
    ).all()]
    m.AttributeGroupAttribute.query.filter(
        m.AttributeGroupAttribute.attribute_group_id == old_dim_group.id
    ).delete(False)
    query.delete(False)

    # create new uom group and dimensional group for each attribute set
    for attr_set in m.AttributeSet.query.all():
        priority = 1000
        # create dimension attribute group
        dim_group = m.AttributeGroup()
        dim_group.name = 'Thông tin kích thước'
        dim_group.code = 'nhom-he-thong'
        dim_group.priority = priority
        dim_group.parent_id = 0
        dim_group.level = 1
        dim_group.is_flat = 0
        dim_group.system_group = 1
        dim_group.attribute_set_id = attr_set.id
        dim_group.path = ''
        m.db.session.add(dim_group)
        m.db.session.flush()
        dim_group.path = dim_group.id

        # add dimension variant attribute to the dimension group
        for index, attr_id in enumerate(dim_attr_ids):
            priority += index + 1
            linked = m.AttributeGroupAttribute()
            linked.attribute_id = attr_id
            linked.attribute_group_id = dim_group.id
            linked.priority = priority
            linked.is_displayed = 1
            linked.is_variation = 0
            m.db.session.add(linked)
            m.db.session.flush()

        priority += 1
        uom_group = m.AttributeGroup()
        uom_group.name = 'Đơn vị tính'
        uom_group.code = 'uom'
        uom_group.priority = priority
        uom_group.parent_id = 0
        uom_group.level = 1
        uom_group.is_flat = 0
        uom_group.attribute_set_id = attr_set.id
        uom_group.system_group = 1
        uom_group.path = ''
        m.db.session.add(uom_group)
        m.db.session.flush()
        uom_group.path = uom_group.id

        # add uom variant attribute and uom_ratio attribute to the uom group
        priority += 1
        linked_uom_attr = m.AttributeGroupAttribute()
        linked_uom_attr.attribute_id = uom_attr.id
        linked_uom_attr.attribute_group_id = uom_group.id
        linked_uom_attr.priority = priority
        linked_uom_attr.is_displayed = 1
        linked_uom_attr.is_variation = 1
        linked_uom_attr.variation_priority = 1
        linked_uom_attr.variation_display_type = 'text'
        m.db.session.add(linked_uom_attr)
        m.db.session.flush()

        priority += 1
        linked_uom_ratio = m.AttributeGroupAttribute()
        linked_uom_ratio.attribute_id = ratio_attr.id
        linked_uom_ratio.attribute_group_id = uom_group.id
        linked_uom_ratio.priority = priority
        linked_uom_ratio.is_displayed = 1
        linked_uom_ratio.is_variation = 0
        m.db.session.add(linked_uom_ratio)
        m.db.session.flush()

    m.db.session.commit()

    # migrate uom code & uom_ratio
    sku_sql = f'UPDATE sellable_products JOIN units on sellable_products.unit_id = units.id ' \
              f'set uom_ratio = 1.0, uom_code = units.code'
    m.db.session.execute(sku_sql)

    # migrate product unit to variant attribute
    sql = f'INSERT INTO variant_attribute (variant_id, attribute_id, value) ' \
          f'SELECT variant_id, {uom_attr.id}, attribute_options.id FROM sellable_products ' \
          f'LEFT JOIN units ON sellable_products.unit_id = units.id ' \
          f'LEFT JOIN attribute_options on units.code = attribute_options.code'
    m.db.session.execute(sql)

    ratio_sql = f'INSERT INTO variant_attribute (variant_id, attribute_id, value) SELECT `id`, {ratio_attr.id}, 1.0 from product_variants'
    m.db.session.execute(ratio_sql)

    # set default uom values to all variants
    variant_sql = f'UPDATE product_variants SET all_uom_ratios = CONCAT(`id`, ":1.0,")'
    m.db.session.execute(variant_sql)
