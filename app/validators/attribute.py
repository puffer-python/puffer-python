#coding=utf-8

from catalog import (
    models,
    utils,
)
from catalog.extensions import exceptions as exc
from . import Validator



class CreateAttributeValidator(Validator):
    @staticmethod
    def validate_data(name, code, unit_id=None, obj_id=None, **kwargs):
        errors = list()
        if utils.contain_special_char(name):
            raise exc.BadRequestException('Tên thuộc tính chứa kí tự đặc biệt')
        exist_name = models.Attribute.query.filter(
            models.Attribute.name == name
        )
        if obj_id:
            exist_name = exist_name.filter(models.Attribute.id != obj_id)
        if exist_name.first():
            errors.append({'field': 'name',
                           'message': 'Tên thuộc tính đã tồn tại'})

        exist_code = models.Attribute.query.filter(
            models.Attribute.code == code,
        )
        if obj_id:
            exist_code = exist_code.filter(models.Attribute.id != obj_id)
        if exist_code.first():
            errors.append({'field': 'code',
                           'message': 'Mã thuộc tính đã tồn tại'})

        if unit_id:
            unit = models.ProductUnit.query.get(unit_id)
            if not unit:
                errors.append({'name': 'unit',
                               'message': 'Đơn vị tính không tồn tại'})
        if bool(errors):
            raise exc.BadRequestException(
                message='Dữ liệu không thỏa mãn',
                errors=errors
            )

    @staticmethod
    def validate_value_type(value_type, **kwargs):
        value_type_support = ('number', 'text', 'selection', 'multiple_select')
        if value_type not in value_type_support:
            raise exc.BadRequestException(
                f'Kiếu giá trị không nằm trong các kiểu {", ".join(value_type_support)}')

    @staticmethod
    def validate_filterable(is_filterable=None, value_type=None, **kwargs):
        if is_filterable is not None and value_type is not None:
            filterable_support = ('multiple_select', 'selection')
            if is_filterable and value_type not in filterable_support:
                raise exc.BadRequestException(
                    f'Chỉ filterable với thuộc tính kiểu {",".join(filterable_support)}')


class UpdateAttributeValidator(CreateAttributeValidator):
    pass


class AttributeValidator(Validator):
    @staticmethod
    def validate_patch(data, obj_id=None, **kwargs):
        is_filterable = data.get('is_filterable')
        value_type = data.get('value_type')
        filterable_support = ('multiple_select', 'selection')
        if is_filterable and value_type not in filterable_support:
            raise exc.BadRequestException(
                f'Chỉ filterable với thuộc tính kiểu {",".join(filterable_support)}')

    @staticmethod
    def validate_data(data, obj_id=None, **kwargs):
        """_validate_before_save

        :param data:
        :param obj_id:
        """
        errors = {}
        if obj_id:
            exist_name = models.Attribute.query.filter(
                models.Attribute.name == data.get('name'),
                models.Attribute.id != obj_id
            ).first()
            exist_code = models.Attribute.query.filter(
                models.Attribute.code == data.get('code'),
                models.Attribute.id != obj_id
            ).first()
        else:
            exist_name = models.Attribute.query.filter(
                models.Attribute.name == data.get('name'),
            ).first()

            exist_code = models.Attribute.query.filter(
                models.Attribute.code == data.get('code'),
            ).first()
        unit_id = data.get('unit_id')
        if unit_id:
            exist_unit = models.ProductUnit.query.get(unit_id)
            if not exist_unit:
                errors['unit'] = 'Đơn vị tính không tồn tại'

        if exist_name:
            errors['name'] = 'Tên thuộc tính đã tồn tại'
        if exist_code:
            errors['code'] = 'Mã thuộc tính đã tồn tại'
        if bool(errors):
            raise exc.BadRequestException(errors=errors)
