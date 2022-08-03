# coding=utf-8
import itertools

from sqlalchemy import or_, and_, func
from flask_login import current_user
from catalog import models as m
from catalog.services import Singleton
from catalog.extensions import signals
from catalog.constants import FULLFILLMENT_BY_SELLER
from catalog.services import seller as seller_srv
from .attribute_query import AttributeQuery


class AttributeService(Singleton):
    def get_attribute_list(self, filters=None, sort_field=None, sort_order='ascend', page=1,
                           page_size=10, return_full=False):
        """get_attribute_list

        :param filters:
        :param sort_field:
        :param sort_order:
        :param page:
        :param page_size:
        :param return_full:
        """
        query = AttributeQuery()
        if filters:
            query.apply_filters(filters)
        total_record = len(query)
        query.pagination(page, page_size)
        if return_full:
            return query.all(), total_record
        return query.all()

    def get_attribute(self, attribute_id):
        """get_attribute
        Get attribute by id

        :param attribute_id:
        """
        return m.Attribute.query.get(attribute_id)

    def create_attribute(self, data):
        """create_attribute

        :param data:
        """
        attribute = m.Attribute(**data)
        m.db.session.add(attribute)
        m.db.session.commit()
        return attribute

    def update_attribute(self, attribute_id, data):
        """update_attribute

        :param attribute_id:
        :param data:
        """
        is_change = False
        attribute = m.Attribute.query.get(attribute_id)
        if attribute:
            for field, value in data.items():
                if hasattr(attribute, field):
                    is_change = is_change or getattr(attribute, field) != value
                    setattr(attribute, field, value)
        if is_change:
            signals.attribute_updated_signal.send(attribute)
        m.db.session.commit()
        return attribute

    def create_attribute_option(self, attribute_id, data):
        """create a new attribute option

        :param attribute_id: int
        :param data: dict
        """

        option = m.AttributeOption(
            attribute_id=attribute_id,
            code=data.get('code'),
            value=data.get('value'),
            seller_id=current_user.seller_id,
        )

        m.db.session.add(option)
        m.db.session.commit()

        return option

    def update_attribute_option(self, option_id, data):
        """Update an attribute option
        :param option_id: int
        :param data: dict
        """

        option = m.AttributeOption.query.filter(
            m.AttributeOption.id == option_id
        ).first()
        if option.value == data.get('value'):
            return
        if 'value' in data:
            option.value = data['value']
            signals.attribute_option_updated_signal.send(option)
            m.db.session.commit()

    def delete_attribute_option(self, option_id):
        """Delete an attribute option
        :param option_id: int
        """

        m.AttributeOption.query.filter(
            m.AttributeOption.id == option_id
        ).delete(synchronize_session=False)

        m.db.session.commit()

    def get_list_attribute_options(self, attribute_id, filters, page=1, page_size=10):
        """Get list attribute options
        :param attribute_id: int
        :param filters: dict
        :param page: int
        :param page_size: int
        """

        be_page_size = 100

        seller = seller_srv.get_seller_by_id(current_user.seller_id)

        if seller['servicePackage'] == FULLFILLMENT_BY_SELLER:
            available_seller_id = current_user.seller_id
        else:
            available_seller_id = 0

        query = m.AttributeOption.query.filter(
            m.AttributeOption.attribute_id == attribute_id,
            m.AttributeOption.seller_id == available_seller_id,
        )

        ids = filters.get('ids')
        if ids:
            query = query.filter(
                m.AttributeOption.id.in_(ids)
            )

        codes = filters.get('codes')
        if codes:
            query = query.filter(
                m.AttributeOption.code.in_(codes)
            )

        keyword = filters.get('keyword')  # name or code
        if keyword:
            query = query.filter(or_(
                m.AttributeOption.code.like(f'%{keyword}%'),
                m.AttributeOption.value.like(f'%{keyword}%'),
            ))

        total_records = query.count()

        limit = min(be_page_size, page_size)
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        return {
            'current_page': page,
            'page_size': limit,
            'total_records': total_records,
            'options': query.all(),
        }

    def get_options_of_attrs(self, ids):
        options = m.AttributeOption.query.filter(
            m.AttributeOption.attribute_id.in_(ids)
        )
        attrs = itertools.groupby(options, lambda x: x.attribute_id)
        return [{'attribute_id': attr_id, 'options': list(ops)} for attr_id, ops in attrs]

    @staticmethod
    def get_uom_code_by_name(seller_id, uom_name):
        uom_attribute = m.Attribute.query.filter(m.Attribute.code == 'uom').first()
        data = m.db.session.query(m.AttributeOption.code).filter(
            and_(m.AttributeOption.attribute_id == uom_attribute.id,
                 m.AttributeOption.seller_id.in_([0, seller_id]),
                 func.lower(m.AttributeOption.value) == uom_name.lower())
        ).order_by(m.AttributeOption.seller_id.desc()).first()
        if data:
            return data[0]
        return None


attribute_svc = AttributeService.get_instance()
