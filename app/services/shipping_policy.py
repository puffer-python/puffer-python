# coding=utf-8
import logging

from sqlalchemy import func, distinct, and_, or_
from sqlalchemy.orm import lazyload, joinedload

from catalog import models as m
from catalog.extensions import exceptions as exc

__author__ = 'Kien.HT'

from catalog.models import db

from catalog.services import QueryBase
from catalog.services.master_categories import MasterCategoryService

_logger = logging.getLogger(__name__)


def get_shipping_policy(id):
    """

    :param int id:
    :return: a shipping policy matched with id
    :rtype: m.ShippingPolicy
    """
    sp = m.ShippingPolicy.query.filter(
        m.ShippingPolicy.id == id
    ).first()

    if not sp:
        raise exc.NotFoundException(
            'Rule không tồn tại trên hệ thống'
        )

    return sp


def create_shipping_policy(data):
    """

    :param data:
    :return:
    """
    policy = m.ShippingPolicy()
    policy.name = data.get('name')
    policy.is_active = data.get('is_active', True)
    policy.shipping_type = data.get('shipping_type')
    m.db.session.add(policy)
    m.db.session.flush()

    provider_ids = data.get('provider_ids')
    category_ids = data.get('category_ids')
    for provider_id in provider_ids:
        for category_id in category_ids:
            mapping = m.ShippingPolicyMapping()
            mapping.policy_id = policy.id
            mapping.provider_id = provider_id
            mapping.category_id = category_id
            m.db.session.add(mapping)

    m.db.session.commit()
    return policy


class ShippingPolicyListQuery(QueryBase):
    model = m.ShippingPolicy

    def __len__(self):
        count_query = self.query
        count_query = count_query.options(
            lazyload('*')).statement.with_only_columns([func.count(distinct(m.ShippingPolicy.id))]).order_by(
            None).group_by(None)
        return m.db.session.execute(count_query).scalar()

    def apply_filters(self, filters):
        self.query = self.query.group_by(m.ShippingPolicy.id)
        self.query = self.query.order_by(m.ShippingPolicy.updated_at.desc())

        name = filters.get('name')
        if name:
            self.apply_name_filter(name)

        is_active = filters.get('is_active')
        if is_active is not None:
            self.apply_is_active_filter(is_active)

        shipping_type = filters.get('shipping_type')
        if shipping_type:
            self.apply_shipping_type_filter(shipping_type)

        provider_ids = filters.get('provider_ids', '')
        category_ids = filters.get('category_ids', '')
        if provider_ids or category_ids:
            cond_ = and_ if (provider_ids and category_ids) else or_
            self.query = self.query.join(m.ShippingPolicyMapping)
            self.query = self.query.filter(
                cond_(
                    m.ShippingPolicyMapping.provider_id.in_(provider_ids.split(',')),
                    m.ShippingPolicyMapping.category_id.in_(category_ids.split(','))
                )
            )

    def apply_name_filter(self, name):
        self.query = self.query.filter(
            m.ShippingPolicy.name.ilike(f'%{name}%')
        )

    def apply_is_active_filter(self, is_active):
        self.query = self.query.filter(
            m.ShippingPolicy.is_active.is_(is_active)
        )

    def apply_shipping_type_filter(self, shipping_type):
        self.query = self.query.filter(
            m.ShippingPolicy.shipping_type == shipping_type
        )


def get_shipping_policy_list(params):
    """

    :param params:
    :return:
    """
    query = ShippingPolicyListQuery()
    query.apply_filters(params)
    total = len(query)
    page = params.get('page')
    page_size = params.get('page_size')
    query.pagination(page, page_size)
    items = query.all()

    return {
        'page': page,
        'page_size': page_size,
        'total_records': total,
        'policies': items
    }


def get_existed_mapping_records(policy_id):
    """

    :param policy_id:
    :return:
    """
    return m.ShippingPolicyMapping.query.filter(
        m.ShippingPolicyMapping.policy_id == policy_id
    ).all()


def update_shipping_policy(id, data):
    """

    :param data:
    :return:
    """
    updated_fields = dict()
    policy = m.ShippingPolicy.query.get(id)
    if 'name' in data:
        policy.name = data.get('name')
        updated_fields['name'] = policy.name

    if 'provider_ids' or 'category_ids' in data:
        mapping = get_existed_mapping_records(policy.id)
        provider_ids = req_provider_ids = data.get('provider_ids')
        if not req_provider_ids:
            provider_ids = [each.provider_id for each in mapping]
        category_ids = req_category_ids = data.get('category_ids')
        if not req_category_ids:
            category_ids = [each.category_id for each in mapping]

        # delete old records
        m.ShippingPolicyMapping.query.filter(
            m.ShippingPolicyMapping.policy_id == policy.id
        ).delete(False)
        for provider_id in provider_ids:
            for category_id in category_ids:
                mapping = m.ShippingPolicyMapping()
                mapping.policy_id = policy.id
                mapping.category_id = category_id
                mapping.provider_id = provider_id
                m.db.session.add(mapping)

        if req_provider_ids:
            updated_fields['provider_ids'] = req_provider_ids
        if req_category_ids:
            updated_fields['categories'] = m.MasterCategory.query.filter(
                m.MasterCategory.id.in_(req_category_ids)
            ).all()

    if 'shipping_type' in data:
        shipping_type = data.get('shipping_type')
        policy.shipping_type = shipping_type
        updated_fields['shipping_type'] = policy.shipping_type

    if 'is_active' in data:
        is_active = data.get('is_active')
        policy.is_active = is_active
        updated_fields['is_active'] = policy.is_active

    m.db.session.commit()
    return updated_fields


def get_shipping_property_of_sellable_product(sellable_product):
    master_category_service = MasterCategoryService.get_instance()
    master_category = master_category_service.get_master_category(
        sellable_product.master_category_id)

    if master_category is None:
        return 'all'

    master_category_ids = master_category.path.split('/')

    shipping_policy = db.session.query(
        m.ShippingPolicy.shipping_type
    ).join(
        m.ShippingPolicyMapping,
        m.ShippingPolicyMapping.policy_id == m.ShippingPolicy.id
    ).join(
        m.MasterCategory,
        m.MasterCategory.id == m.ShippingPolicyMapping.category_id
    ).filter(
        m.ShippingPolicyMapping.provider_id == sellable_product.provider_id,
        m.ShippingPolicyMapping.category_id.in_(master_category_ids),
        m.ShippingPolicy.is_active.is_(True)
    ).order_by(
        m.MasterCategory.depth.desc()
    ).first()

    return shipping_policy.shipping_type if shipping_policy else 'all'
