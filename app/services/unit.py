# coding=utf-8
import logging

from flask_login import current_user
from sqlalchemy import or_

from catalog import models as m
from catalog.extensions import signals

__author__ = 'Nam.VH'

from catalog.extensions.exceptions import BadRequestException

from catalog.services import QueryBase

_logger = logging.getLogger(__name__)


def sync_to_attribute_option(unit):
    uom_attribute = m.Attribute.query.filter(m.Attribute.code == 'uom').first()
    query = m.AttributeOption.query.filter(
        m.AttributeOption.code == unit.code,
        m.AttributeOption.attribute_id == uom_attribute.id,
        m.AttributeOption.seller_id == unit.seller_id
    )

    option = query.first()

    if option is None:
        option = m.AttributeOption(
            attribute_id=uom_attribute.id,
            code=unit.code,
            value=unit.name,
            seller_id=unit.seller_id,
            display_value=unit.display_name
        )
        m.db.session.add(option)
    else:
        option.value = unit.name
        option.display_value = unit.display_name


def create_unit(data):
    unit = m.Unit()
    unit.name = data.get('name')
    unit.code = data.get('code')
    unit.display_name = data.get('display_name')
    unit.seller_id = current_user.seller_id
    m.db.session.add(unit)
    m.db.session.flush()
    sync_to_attribute_option(unit)
    signals.unit_created_signal.send(unit)
    m.db.session.commit()

    return unit


def update_unit(unit_id, data):
    """update_unit

    :param unit_id:
    :param data:
    """
    unit = m.Unit.query.filter(
        m.Unit.id == unit_id
    ).first()

    update_key = ['name', 'display_name']
    for key in update_key:
        if key in data:
            setattr(unit, key, data.get(key))
    sync_to_attribute_option(unit)
    signals.unit_updated_signal.send(unit)
    m.db.session.commit()

    return unit


def delete_unit(unit_id):
    unit = m.Unit.query.filter(
        m.Unit.id == unit_id
    ).delete(synchronize_session=False)

    signals.unit_deleted_signal.send(unit)
    m.db.session.commit()
    return unit


class UnitListQuery(QueryBase):
    model = m.Unit

    def apply_filters(self, params):
        kw = params.get('query')
        if kw:
            self._apply_keyword_filter(kw)
        self.query = self.query.filter(
            m.Unit.seller_id.in_([0, current_user.seller_id])
        )

    def _apply_keyword_filter(self, kw):
        self.query = self.query.filter(
            or_(m.Unit.name.like('%{}%'.format(kw)), m.Unit.code.like('%{}%'.format(kw)))
        )

    def _apply_sort_order(self):
        self.query = self.query.order_by(m.Unit.id)


def get_list_units(**params):
    page = params.pop('page')
    page_size = params.pop('page_size')

    list_query = UnitListQuery()
    list_query.apply_filters(params)

    total_records = len(list_query)
    list_query.pagination(page, page_size)

    return list_query.all(), total_records
