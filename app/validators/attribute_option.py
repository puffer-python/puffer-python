# coding=utf-8

from sqlalchemy import (
    or_,
    func,
    exists, and_,
)
from sqlalchemy.orm import load_only
from flask_login import current_user
from catalog import models
from catalog.extensions import exceptions as exc
from catalog.services import seller as seller_srv
from catalog.validators import Validator
from catalog.constants import FULLFILLMENT_BY_SELLER


class BaseAttributeOptionValidator:

    def validate(self, data=None):

        data = data or {}

        for fn_name in dir(self):
            if fn_name.startswith('validate_'):
                fn = getattr(self, fn_name)
                fn(**data)

    def _validate_duplicated(self, attribute_id, value=None, code=None, excludes=None, **kwargs):
        """The option is duplicated if code is existed or value is existed
        :param attribute_id: int
        :param value: str, new value for creating or updating
        :param code: str, new value for creating or updating
        :param: excludes: List[int], list of option id, which is excluded when searching duplicated records
        """

        duplicated_cond = []

        if value:
            value_duplicated_cond = func.lower(models.AttributeOption.value) == value.lower()
            duplicated_cond.append(value_duplicated_cond)

        if code:
            code_duplicated_cond = func.lower(models.AttributeOption.code) == code.lower()
            duplicated_cond.append(code_duplicated_cond)

        excludes_cond = True
        if excludes:
            excludes_cond = models.AttributeOption.id.notin_(excludes)

        existed = models.db.session.query(
            models.AttributeOption.query.filter(
                or_(*duplicated_cond),
                excludes_cond,
                models.AttributeOption.attribute_id == attribute_id,
                and_(
                    or_(
                        models.AttributeOption.seller_id == current_user.seller_id,
                        models.AttributeOption.seller_id is None,
                        models.AttributeOption.seller_id == 0,
                    )
                )
            ).exists()
        ).scalar()

        if existed:
            raise exc.BadRequestException('Tùy chọn đã tồn tại')


class CreateAttributeOptionValidator(BaseAttributeOptionValidator):
    def __init__(self, attribute_id):

        attribute = models.Attribute.query.get(attribute_id)
        if not attribute:
            raise exc.BadRequestException('Thuộc tính không tồn tại')

        if attribute.value_type not in ('selection', 'multiple_select'):
            raise exc.BadRequestException('Thuộc tính phải là selection hoặc multiple_select')

        if attribute.code == 'uom':
            # Only fullfillment by seller can create option
            seller = seller_srv.get_seller_by_id(current_user.seller_id)
            servicePackage = seller['servicePackage']
            if servicePackage != FULLFILLMENT_BY_SELLER:
                raise exc.BadRequestException(
                    f'Seller này không thể tạo được tuỳ chọn do đang sử dụng gói dịch vụ {servicePackage}')

        self.attribute = attribute

    def validate_data(self, value, code=None, **kwargs):

        self._validate_duplicated(self.attribute.id, value, code)


class ModifyAttributeOptionValidator(BaseAttributeOptionValidator):

    def __init__(self, attribute_id, option_id):

        option = models.AttributeOption.query.filter(
            models.AttributeOption.id == option_id,
            models.AttributeOption.attribute_id == attribute_id,
            models.AttributeOption.seller_id == current_user.seller_id,
        ).first()
        if not option:
            raise exc.BadRequestException(
                'Tuỳ chọn không tồn tại hoặc tuỳ chọn không có trong thuộc tính này'
            )

        used_exc = exc.BadRequestException(f'Tuỳ chọn {option.value} đang được sử dụng, không thể sửa/xoá')

        used = models.db.session.query(
            models.VariantAttribute.query.join(
                models.Attribute,
                models.Attribute.id == models.VariantAttribute.attribute_id
            ).filter(
                models.Attribute.value_type.in_(['selection', 'multiple_select']),
                or_(
                    # option is used by selection attribute
                    models.VariantAttribute.value == option.id,

                    # option is used by multiple select attribute
                    models.VariantAttribute.value.like(f'{option.id},%'),
                    models.VariantAttribute.value.like(f'%,{option.id}'),
                    models.VariantAttribute.value.like(f'%,{option.id},%'),
                )
            ).exists()
        ).scalar()
        if used:
            raise used_exc

        if option.code is not None:
            used = models.db.session.query(
                models.SellableProduct.query.filter(
                    models.SellableProduct.uom_code == option.code
                ).options(
                    load_only('id', 'uom_code')
                ).exists()
            ).scalar()

            if used:
                raise used_exc

            self.option = option
            self.attribute_id = attribute_id


class UpdateAttributeOptionValidator(ModifyAttributeOptionValidator):

    def validate_duplicated(self, value=None, **kwargs):
        self._validate_duplicated(self.attribute_id, value, excludes=[self.option.id])


class DeleteAttributeOptionValidator(ModifyAttributeOptionValidator):
    pass
