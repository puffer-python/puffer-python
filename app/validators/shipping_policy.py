# coding=utf-8
import logging

from flask_login import current_user
from sqlalchemy import exists, and_

from catalog import models as m
from catalog.extensions import exceptions as exc
from catalog.services import provider as provider_srv
from catalog.validators import Validator

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateShippingPolicyValidator(Validator):
    @staticmethod
    def validate_policy_name(name, **kwargs):
        """
        Check whether name existed in database

        :param name:
        :param kwargs:
        :return:
        """
        existed = m.db.session.query(
            exists().where(and_(
                m.ShippingPolicy.name.ilike(f'%{name}%'),
                m.ShippingPolicy.is_active.is_(True)
            ))
        ).scalar()

        if existed:
            raise exc.BadRequestException(
                'Shipping rule name đã tồn tại'
            )

    @staticmethod
    def validate_providers(provider_ids, **kwargs):
        """
        Check whether the provider_codes are all valid:
            - Is a list of integer(marshmallow).
            - Existed in database and hasn't been deactivated.

        :param list[int] provider_ids:
        :param kwargs:
        :return: None
        """

        def _provider_existed(prov_id):
            return m.db.session.query(
                exists().where(and_(
                    m.Provider.id == prov_id,
                    m.Provider.is_active.is_(True)
                ))
            ).scalar()

        err = [id for id in provider_ids if not _provider_existed(id)]
        if err:
            raise exc.BadRequestException(
                message='Provider không tồn tại hoặc đã bị vô hiệu',
                errors=err
            )

    @staticmethod
    def validate_categories(category_ids, **kwargs):
        """
        Check whether the categories_codes are valid:
            - Is a list of integer(marshmallow).
            - Existed in database.

        :param list[int] category_ids:
        :param kwargs:
        :return: None
        """

        def _category_existed(cat_id):
            return m.db.session.query(
                exists().where(and_(
                    m.MasterCategory.id == cat_id
                ))
            ).scalar()

        err = [id for id in category_ids if not _category_existed(id)]
        if err:
            raise exc.BadRequestException(
                message='Danh mục không tồn tại',
                errors=err
            )

    @staticmethod
    def validate_shipping_type(shipping_type, **kwargs):
        """
        Check if shipping_type is of ALL|NEAR|BULKY(get from misc).

        :param str shipping_type:
        :param kwargs:
        :return:
        """
        existed = m.db.session.query(
            exists().where(and_(
                m.Misc.type == 'shipping_type',
                m.Misc.code == shipping_type
            ))
        ).scalar()

        if not existed:
            raise exc.BadRequestException(
                message='Shipping type không hợp lệ',
                errors=shipping_type
            )

    @staticmethod
    def validate_same_policy_existed(provider_ids, category_ids, **kwargs):
        existed = m.db.session.query(
            exists().where(and_(
                m.ShippingPolicyMapping.category_id.in_(category_ids),
                m.ShippingPolicyMapping.provider_id.in_(provider_ids)
            ))
        ).scalar()
        if existed:
            raise exc.BadRequestException('Shipping policy đã tồn tại')


class UpdateShippingPolicyValidator(Validator):
    @staticmethod
    def validate_update_policy(obj_id, **kwargs):
        policy = m.ShippingPolicy.query.get(obj_id)
        if not policy:
            raise exc.BadRequestException('Policy not exists.')

        name = kwargs.get('name')
        if name:
            UpdateShippingPolicyValidator._validate_policy_name(
                policy_id=obj_id,
                name=name
            )

        provider_ids = kwargs.get('provider_ids')
        if provider_ids:
            UpdateShippingPolicyValidator._validate_providers(
                provider_ids
            )

        category_ids = kwargs.get('category_ids')
        if category_ids:
            UpdateShippingPolicyValidator._validate_categories(
                category_ids
            )

        shipping_type = kwargs.get('shipping_type')
        if shipping_type:
            UpdateShippingPolicyValidator._validate_shipping_type(
                shipping_type
            )

    @staticmethod
    def _validate_policy_name(policy_id, name, **kwargs):
        """
        Check whether name existed in database
        :param policy_id:
        :param name:
        :param kwargs:
        :return:
        """
        existed = m.db.session.query(
            exists().where(and_(
                m.ShippingPolicy.name.ilike(f'%{name}%'),
                m.ShippingPolicy.is_active.is_(True),
                m.ShippingPolicy.id != policy_id
            ))
        ).scalar()

        if existed:
            raise exc.BadRequestException(
                'Shipping rule name đã tồn tại'
            )

    @staticmethod
    def _validate_providers(provider_ids, **kwargs):
        """
        Check whether the provider_codes are all valid:
            - Is a list of integer(marshmallow).
            - Existed in database and hasn't been deactivated.

        :param list[int] provider_codes:
        :param kwargs:
        :return: None
        """

        def _provider_existed(provider_id):
            provider = provider_srv.get_provider_by_id(provider_id)
            if provider and provider.get('sellerID') == current_user.seller_id and provider.get('isActive'):
                return provider.get('id')

        err = [id for id in provider_ids if not _provider_existed(id)]
        if err:
            raise exc.BadRequestException(
                message='Provider không tồn tại hoặc đã bị vô hiệu',
                errors=err
            )

    @staticmethod
    def _validate_categories(category_ids, **kwargs):
        """
        Check whether the categories_codes are valid:
            - Is a list of integer(marshmallow).
            - Existed in database.

        :param list[int] category_ids:
        :param kwargs:
        :return: None
        """

        def _category_existed(id):
            return m.db.session.query(
                exists().where(and_(
                    m.MasterCategory.id == id
                ))
            ).scalar()

        err = [id for id in category_ids if not _category_existed(id)]
        if err:
            raise exc.BadRequestException(
                message='Danh mục không tồn tại hoặc đã bị vô hiệu',
                errors=err
            )

    @staticmethod
    def _validate_shipping_type(shipping_type, **kwargs):
        """
        Check if shipping_type is of all|near|bulky(get from misc).

        :param str shipping_type:
        :param kwargs:
        :return:
        """
        existed = m.db.session.query(
            exists().where(and_(
                m.Misc.type == 'shipping_type',
                m.Misc.code == shipping_type
            ))
        ).scalar()

        if not existed:
            raise exc.BadRequestException(
                message='Shipping type không hợp lệ',
                errors=shipping_type
            )
