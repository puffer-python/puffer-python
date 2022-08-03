# coding=utf-8
import funcy
import time
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import (
    joinedload,
    load_only,
)
from catalog import utils
from catalog import models as m
from catalog.services.attribute_sets import AttributeSetBaseService
from catalog.services import Singleton
from catalog.extensions import exceptions as exc, signals
from flask_login import current_user
from .query import AttributeSetListQuery
from catalog.constants import (UOM_CODE_ATTRIBUTE, UOM_RATIO_CODE_ATTRIBUTE)

import logging

from ...models import MANUFACTURE_CODE

_logger = logging.getLogger(__name__)


def get_variant_attribute_by_attribute_set_id(set_id):
    """
    Author: dung.bv
    Created At: 2021-11-30
    Function get all variant attribute by id
    Return a list of variant
    Default return empty array
    """
    return m.Attribute.query.join(
        m.AttributeGroupAttribute,
        m.AttributeGroupAttribute.attribute_id == m.Attribute.id
    ).join(
        m.AttributeGroup,
        m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
    ).filter(
        m.AttributeGroup.attribute_set_id == set_id,
        m.AttributeGroupAttribute.is_variation is True,
        m.Attribute.code.notin_([UOM_CODE_ATTRIBUTE, UOM_RATIO_CODE_ATTRIBUTE])
    ).order_by(m.Attribute.id).all()


def get_manufacture_attribute():
    manufacture_attribute = m.Attribute.query.filter(m.Attribute.code == MANUFACTURE_CODE).first()
    if manufacture_attribute:
        return manufacture_attribute.options
    return []


def get_normal_attribute(attribute_set_id):
    attribute_ids = m.Attribute.query.join(
        m.AttributeGroupAttribute,
        m.AttributeGroupAttribute.attribute_id == m.Attribute.id
    ).join(
        m.AttributeGroup,
        m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
    ).filter(
        and_(
            or_(
                m.AttributeGroup.system_group == 0,
                m.AttributeGroup.system_group.is_(None)
            ),
            m.Attribute.code != 'uom',
            m.AttributeGroup.attribute_set_id == attribute_set_id
        )
    ).all()  # type: list[m.Attribute]

    return m.Attribute.query.filter(m.Attribute.id.in_(
        funcy.lpluck_attr('id', attribute_ids)
    ))  # type: list[m.Attribute]


def get_default_system_attribute_set():
    return m.AttributeSet.query.join(
        m.AttributeGroup,
        m.AttributeGroup.attribute_set_id == m.AttributeSet.id
    ).filter(
        m.AttributeGroup.system_group.is_(True)
    ).with_entities(m.AttributeSet.id).first()

def get_system_attributes():
    attribute_set = get_default_system_attribute_set()
    if not attribute_set:
        return []
    attributes = m.db.session.query(m.AttributeGroupAttribute).join(
        m.AttributeGroup,
        m.AttributeGroupAttribute.attribute_group_id == m.AttributeGroup.id
    ).join(
        m.Attribute,
        m.Attribute.id == m.AttributeGroupAttribute.attribute_id
    ).filter(
        m.Attribute.code.notin_(['uom', 'uom_ratio', ]),
        m.AttributeGroup.attribute_set_id == attribute_set.id
    ).options(
        load_only('is_variation'),
        joinedload('attribute_group').load_only('system_group'),
        joinedload('attribute').load_only('id', 'name', 'display_name', 'code', 'value_type', 'is_unsigned').options(
            joinedload('options').load_only('id', 'value')
        )
    ).order_by(m.AttributeGroup.priority, m.AttributeGroupAttribute.priority).all()
    return attributes


class AttributeSetService(Singleton, AttributeSetBaseService):
    SAVE_ATTRIBUTE_GROUP_RETRY_TIMES = 3
    SAVE_ATTRIBUTE_GROUP_RETRY_DELAY_SECONDS = 5

    def get_attribute_set_content(self, attribute_set_id):
        attribute_set = m.AttributeSet.query.get(attribute_set_id)  # type: m.AttributeSet
        if not attribute_set:
            raise exc.BadRequestException(
                f'Không tồn tại bộ thuộc tính có id {attribute_set_id}'
            )

        attribute_set.groups = list(attribute_set.groups)

        attributes = self.get_attributes_of_attribute_set(
            [group.id for group in attribute_set.groups]
        )
        setattr(attribute_set, 'attributes', attributes)

        has_product = False
        product = m.Product.query.filter(
            m.Product.attribute_set_id == attribute_set.id
        ).first()
        if product:
            has_product = True
        setattr(attribute_set, 'has_product', has_product)

        return attribute_set

    def get_attributes_of_attribute_set(self, group_ids):
        """
        Return all attributes of an attribute set
        Thanks to attribute_set -> groups -> attributes relation, we can get
        all attributes of a set by querying all attributes of groups of this set.

        :param list[int] group_ids:
        :return:
        """
        attributes = m.Attribute.query.join(
            m.AttributeGroupAttribute
        ).filter(
            m.Attribute.id == m.AttributeGroupAttribute.attribute_id,
            m.AttributeGroupAttribute.attribute_group_id.in_(group_ids)
        ).all()

        for attribute in attributes:
            attr_info = m.AttributeGroupAttribute.query.filter(
                m.AttributeGroupAttribute.attribute_group_id.in_(group_ids),
                m.AttributeGroupAttribute.attribute_id == attribute.id
            ).first()
            setattr(attribute, 'attr_info', attr_info)

        return attributes or []

    def get_attribute_set_list(self, filters, sort_field, sort_order, page, page_size):
        query = AttributeSetListQuery()
        query.apply_filters(filters)
        if sort_field:
            query.sort(sort_field, sort_order)
        total_records = len(query)
        query.pagination(page, page_size)
        return query.all(), total_records

    # @cache.memoize(300)
    def get_attribute_set(self, attribute_set_id):
        return m.AttributeSet.query.get(attribute_set_id)

    def create_attribute_set(self, data):
        """https://confluence.teko.vn/pages/viewpage.action?pageId=81362963"""
        attribute_set = m.AttributeSet(**data)
        attribute_set.code = utils.slugify(
            utils.convert(attribute_set.name),
            '_'
        )
        attribute_set.created_by = current_user.email
        m.db.session.add(attribute_set)
        m.db.session.commit()

        signals.attribute_set_created_signal.send(attribute_set.id)
        return attribute_set

    def update_attribute_set(self, set_id, data):
        """
        Cập nhật thông tin attribute set.

        Dữ liệu attribute set trong các bảng attribute_group_attribute và
        attribute_groups sẽ được xóa đi và insert lại từ đầu. Chi tiết
        xem tại link:
            https://confluence.teko.vn/pages/viewpage.action?pageId=107249729

        :param int attribute_set_id:
        :param list[dict] attribute_set_configs:
        :return:
        """
        _map = {}
        groups_data = sorted(data, key=lambda k: k['priority'])
        self._check_seo_config(set_id, data)
        try:
            variation_attribute_ids = self._remove_attribute_set_configs(set_id)
            for group_data in groups_data:
                old_group = m.AttributeGroup.query.filter(m.AttributeGroup.id == group_data['temp_id']).first()
                if old_group and old_group.system_group:
                    group = self._update_system_group(old_group, group_data)
                else:
                    group = self._save_group(set_id, group_data, variation_attribute_ids)
                _map.update({
                    group_data['temp_id']: group
                })
                parent_id = group_data['parent_id']
                if parent_id:
                    parent = _map[group_data['parent_id']]
                    group.level = parent.level + 1
                    group.path = '{}/{}'.format(parent.path, group.id)
                    group.parent_id = parent.id
                else:
                    group.level = 1
                    group.path = group.id

            attr_set = m.AttributeSet.query.get(set_id)  # type: m.AttributeSet
            attr_set.updated_at = func.now()
            retry_time = 0
            exc = None
            while retry_time < self.SAVE_ATTRIBUTE_GROUP_RETRY_TIMES:
                try:
                    m.db.session.commit()
                    exc = None
                    break
                except Exception as e:
                    retry_time += 1
                    exc = e
                    time.sleep(self.SAVE_ATTRIBUTE_GROUP_RETRY_DELAY_SECONDS)
            if exc:
                raise exc

        except Exception as e:
            m.db.session.rollback()
            raise exc.BadRequestException(str(e))
        else:
            return attr_set

    def get_config(self, config_id):
        config = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.id == config_id,
            m.AttributeSetConfig.id
        ).first()
        if config is None:
            raise exc.BadRequestException('Config ID incorrect')
        attribute_set = config.attribute_set
        brand = config.brand
        res = {
            'attribute_set_name': attribute_set.name if attribute_set else None,
            'brand_name': brand.name if brand else None,
            'is_default': config.is_default
        }
        # @TODO: use list ob object
        for i in range(1, 6):
            res[f'attribute_{i}_name'] = config.attributes[i - 1].get('name')
            res[f'attribute_{i}_value'] = config.attributes[i - 1].get('value')
        return res

    def get_config_defails(self, config_id, field_display=None):
        """get_config_defails

        :param config_id:
        :param field_display:
        """
        query = m.AttributeSetConfigDetail.query
        if field_display:
            query = query.filter(
                m.AttributeSetConfigDetail.field_display.in_(
                    field_display.split(',')
                )
            )
        query = query.filter(
            m.AttributeSetConfigDetail.attribute_set_config_id == config_id,
        )
        return query.all()

    def get_attributes(self, attribute_set_id):
        attributes = m.Attribute.query.join(
            m.AttributeGroupAttribute,
            m.AttributeGroupAttribute.attribute_id == m.Attribute.id
        ).join(
            m.AttributeGroup,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
        ).filter(
            m.AttributeGroup.attribute_set_id == attribute_set_id
        ).all()

        return attributes

    def get_attributes_with_filter(self, set_id, value_type=None, is_variation=None):
        query = m.AttributeGroupAttribute.query
        query = query.join(
            m.Attribute,
            m.Attribute.id == m.AttributeGroupAttribute.attribute_id
        )
        query = query.join(
            m.AttributeGroup,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
        )
        query = query.filter(
            m.AttributeGroup.attribute_set_id == set_id
        )
        if is_variation is not None:
            query = query.filter(
                m.AttributeGroupAttribute.is_variation.is_(is_variation)
            )
        if value_type is not None:
            query = query.filter(m.Attribute.value_type == value_type)
        query = query.order_by(
            m.AttributeGroupAttribute.variation_priority.asc()
        )
        return query.all()

    def create_attribute_variation(self, attribute_set_id, attribute_id,
                                   variation_display_type):
        """create_attribute_variation

        :param attribute_set_id:
        :param attribute_id:
        :param variation_display_type:
        """
        instance = m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.attribute_id == attribute_id
        ).join(m.AttributeGroup).filter(
            m.AttributeGroup.attribute_set_id == attribute_set_id
        ).first()

        # get variation with maximum priority
        max_priority = m.db.session.query(
            func.max(m.AttributeGroupAttribute.variation_priority)
        ).join(m.AttributeGroup).filter(
            m.AttributeGroup.attribute_set_id == attribute_set_id,
            m.AttributeGroupAttribute.is_variation == 1
        ).scalar()

        instance.variation_priority = (max_priority or 0) + 1
        instance.is_variation = 1
        instance.variation_display_type = variation_display_type
        m.db.session.commit()
        return instance

    def update_order_variation_attribute(self, set_id, ids):
        variation_attrs = self.get_attributes_with_filter(set_id, is_variation=True)
        for attr in variation_attrs:
            attr.variation_priority = ids.index(attr.attribute_id) + 1
        m.db.session.commit()
        return variation_attrs
