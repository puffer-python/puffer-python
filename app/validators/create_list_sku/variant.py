# coding=utf-8
from catalog.utils import safe_cast
from catalog import constants, models as m
from catalog.extensions import exceptions as exc
from catalog.validators.variant import CreateVariantValidator


class UpsertVariantValidator:
    _variant_attribute_validator = CreateVariantValidator()

    @classmethod
    def _get_map_attributes(cls, attribute_set_id):
        group_attributes = m.db.session.query(
            m.AttributeGroupAttribute.attribute_id,
            m.AttributeGroupAttribute.is_variation,
            m.Attribute.value_type
        ).join(
            m.AttributeGroup,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
        ).join(
            m.Attribute,
            m.Attribute.id == m.AttributeGroupAttribute.attribute_id
        ).filter(
            m.AttributeGroup.attribute_set_id == attribute_set_id
        ).all()
        map_variant_attributes = {}
        for attribute_id, is_variation, value_type in group_attributes:
            map_variant_attributes[attribute_id] = (is_variation, value_type)
        return map_variant_attributes

    @classmethod
    def __validate_uom_option(cls, uom_attribute, uom_option_id):
        option = m.AttributeOption.query.filter(m.AttributeOption.attribute_id == uom_attribute.id,
                                                m.AttributeOption.id == uom_option_id).count()
        if not option:
            raise exc.BadRequestException('Đơn vị tính không tồn tại')

    @classmethod
    def get_attributes(cls, variants, map_variant_attributes):
        def _get_value_by_type(value, value_type):
            if value is None:
                return None
            if value_type == constants.ATTRIBUTE_TYPE.TEXT:
                return value
            if value_type == constants.ATTRIBUTE_TYPE.NUMBER:
                try:
                    return int(value)
                except:
                    try:
                        return float(value)
                    except:
                        raise exc.BadRequestException('Giá trị thuộc tính không phải là kiểu số')
            if value_type == constants.ATTRIBUTE_TYPE.SELECTION:
                return safe_cast(value, int)
            return list(map(lambda x: safe_cast(x, int), value.split(',')))

        uom_attribute = m.Attribute.query.filter(
            m.Attribute.code == constants.UOM_CODE_ATTRIBUTE
        ).first()
        uom_ratio_attribute = m.Attribute.query.filter(
            m.Attribute.code == constants.UOM_RATIO_CODE_ATTRIBUTE
        ).first()
        global_variants = []
        format_variants = []
        has_variant_attribute = False
        for v in variants:
            non_variant_attributes = []
            variant_attributes = []
            if not v.get('variant_id') and v.get('uom_id'):
                cls.__validate_uom_option(uom_attribute, v.get('uom_id'))
                variant_attributes.append({'id': uom_attribute.id, 'value': v.get('uom_id')})
                variant_attributes.append({'id': uom_ratio_attribute.id, 'value': v.get('uom_ratio')})
            attributes = v.get('attributes') or []
            for a in attributes:
                if not map_variant_attributes.get(a.get('id')):
                    raise exc.BadRequestException('Thuộc tính không tồn tại hoặc không thuộc bộ thuộc tính được chọn')
                is_variation, value_type = map_variant_attributes.get(a.get('id'))
                item = {
                    'id': a.get('id'),
                    'value': _get_value_by_type(a.get('value'), value_type)
                }
                if is_variation:
                    variant_attributes.append(item)
                else:
                    non_variant_attributes.append(item)
            if v.get('variant_id') and variant_attributes:
                raise exc.BadRequestException('Không được phép cập nhật thuộc tính biến thể')
            if variant_attributes:
                has_variant_attribute = True
            global_variants.append(
                (variant_attributes, non_variant_attributes, v.get('variant_id'))
            )
            if variant_attributes:
                format_variants.append({
                    'attributes': variant_attributes
                })
        return global_variants, format_variants, has_variant_attribute

    @classmethod
    def validate(cls, product_id, attribute_set_id, variants, common_data):
        map_variant_attributes = cls._get_map_attributes(attribute_set_id)
        global_variants, format_variants, has_variant_attribute = cls.get_attributes(variants, map_variant_attributes)
        if has_variant_attribute:
            cls._variant_attribute_validator.validate({'data': {'product_id': product_id, 'variants': format_variants},
                                                       'seller_id': common_data.get('seller_id'),
                                                       'created_by': common_data.get('created_by')})
        return global_variants
