# coding=utf-8
import logging
import re

from catalog import models
from catalog.extensions import exceptions as exc

from . import Validator

__author__ = 'ThanhNK'
_logger = logging.getLogger(__name__)


class BrandValidator(Validator):
    @staticmethod
    def _validate_brand_name(name, current_brand=None):
        """
        Tên thương hiệu không được trùng với tên thương hiệu khác
        đang Hiệu lực trong hệ thống:
            - Không phân biệt hoa thường
            - Có phân biệt tiếng việt có dấu
        :param name:
        :param current_brand:
        :param kwargs:
        :return:
        """
        if name is not None:
            query = models.Brand.query.filter(
                models.Brand.name.ilike(name),
                models.Brand.is_active.is_(True)
            )
            if current_brand:
                query = query.filter(
                    models.Brand.id != current_brand.id,
                )
            if query.first():
                raise exc.BadRequestException('Tên thương hiệu đã tồn tại trong hệ thống')

    @staticmethod
    def _validate_brand_code(code, current_brand=None):
        """
        Validate brand code không cho phép trùng với thương hiệu khác

        :param current_brand:
        :param code:
        :param kwargs:
        """
        pattern = r'(^[a-z0-9][a-z0-9\-]{0,253}[a-z0-9]$)|(^[a-z0-9]{1,255}$)'
        if not re.fullmatch(pattern, code):
            raise exc.BadRequestException(
                'Mã thương hiệu không đúng định dạng'
            )
        # SQL not support sensitive case filter
        query = models.Brand.query.filter(models.Brand.code == code)
        if current_brand is not None:
            query = query.filter(
                models.Brand.id != current_brand.id,
                models.Brand.code != current_brand.code,
            )
        if any([brand.code == code for brand in query.all()]):
            raise exc.BadRequestException(
                'Mã thương hiệu đã tồn tại trong hệ thống'
            )


class CreateBrandValidator(BrandValidator):
    @staticmethod
    def validate_create_brand(**kwargs):
        BrandValidator._validate_brand_name(kwargs.get('name'))
        BrandValidator._validate_brand_code(kwargs.get('code'))


class UpdateBrandValidator(BrandValidator):
    @staticmethod
    def validate_update_brand(**kwargs):
        if 'code' in kwargs:
            raise exc.BadRequestException(
                'Không được phép cập nhật mã thương hiệu!'
            )

        brand = models.Brand.query.filter(
            models.Brand.id == kwargs.get('obj_id')
        ).first()
        validate_required = kwargs.get('is_active') or brand.is_active
        if validate_required:
            BrandValidator._validate_brand_name(
                name=kwargs.get('name'),
                current_brand=brand
            )
        if kwargs.get('is_active'):
            BrandValidator._validate_brand_code(
                code=brand.code,
                current_brand=brand
            )
