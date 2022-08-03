import re

from flask_login import current_user
from sqlalchemy import func, or_, and_

from catalog import models as m
from catalog import validators
from catalog.extensions import exceptions as exc
from catalog.models import SellableProduct, Product


class BaseUnitsValidator(validators.Validator):
    @staticmethod
    def validate_unit_id(obj_id, **kwargs):
        unit = m.Unit.query.get(obj_id)

        if not unit:
            raise exc.BadRequestException('Tên đơn vị tính không tồn tại')


class CreateUnitsValidator(validators.Validator):
    @staticmethod
    def validate_name(name, **kwargs):
        unit = m.Unit.query.filter(and_(
            func.lower(m.Unit.name) == str(name).lower(),
            m.Unit.seller_id == current_user.seller_id
        )
        ).first()

        if unit:
            raise exc.BadRequestException('Tên đơn vị tính đã tồn tại')

    @staticmethod
    def validate_code(code, **kwargs):
        pattern = re.compile("^[A-Za-z0-9]+$")

        if not pattern.match(code):
            raise exc.BadRequestException('Mã đơn vị không được nhập ký tự đặc biệt, hoặc tiếng việt có dấu')

        unit = m.Unit.query.filter(and_(
            func.lower(m.Unit.code) == str(code).lower(),
            m.Unit.seller_id == current_user.seller_id
        )
        ).first()

        if unit:
            raise exc.BadRequestException('Mã đơn vị tính đã tồn tại')


class UpdateUnitsValidator(validators.Validator):

    @staticmethod
    def validate_name(obj_id, name=False, **kwargs):
        if name is None or name == '':
            raise exc.BadRequestException('Tên đơn vị tính không được bỏ trống')
        if name:
            unit = m.Unit.query.filter(
                func.lower(m.Unit.name) == str(name).lower(),
                m.Unit.seller_id == current_user.seller_id,
                m.Unit.id != obj_id
            ).first()

            if unit:
                raise exc.BadRequestException('Tên đơn vị tính đã tồn tại')

    @staticmethod
    def validate_permission(obj_id, **kwargs):
        unit = m.Unit.query.get(obj_id)

        if not unit or unit.seller_id not in (0, current_user.seller_id):
            raise exc.BadRequestException('Đơn vị tính không tồn tại hoặc bạn không có quyền sửa đơn vị tính này')


class DeleteUnitsValidator(BaseUnitsValidator):
    @staticmethod
    def validate_in_sellable_products(obj_id, **kwargs):
        unit = SellableProduct.query.filter(
            or_(SellableProduct.unit_id == obj_id, SellableProduct.unit_po_id == obj_id)
        ).first()

        if unit:
            raise exc.BadRequestException(
                'Không thể xóa, đơn vị tính đang được sử dụng'
            )

    @staticmethod
    def validate_in_products(obj_id, **kwargs):
        unit = Product.query.filter(
            or_(Product.unit_id == obj_id, Product.unit_po_id == obj_id)
        ).first()

        if unit:
            raise exc.BadRequestException(
                'Không thể xóa, đơn vị tính đang được sử dụng'
            )
