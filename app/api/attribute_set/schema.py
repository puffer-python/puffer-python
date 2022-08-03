# coding=utf-8
import logging
from marshmallow import fields as origin_fields
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api import (
    ListParamBase,
    ListResponseBase,
    SortableParam,
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class AttributeOption(Schema):
    id = fields.Integer()
    code = fields.String()
    value = fields.String()
    thumbnail_url = fields.String()


class Attribute(Schema):
    id = fields.Integer()
    name = fields.String(attribute='name_has_unit')
    display_name = fields.String()
    value_type = fields.String()
    code = fields.String()
    options = fields.List(
        fields.Nested(AttributeOption),
        attribute='select_options', default=[])
    unit_id = fields.Integer()
    description = fields.String()
    is_required = fields.Boolean()
    is_system = fields.Boolean()
    is_searchable = fields.Boolean()
    is_filterable = fields.Boolean()
    is_comparable = fields.Boolean()
    is_variation = fields.Boolean(attribute='attr_info.is_variation')
    is_displayed = fields.Boolean(attribute='attr_info.is_displayed')
    priority = fields.Integer(attribute='attr_info.priority')
    variation_priority = fields.Integer(attribute='attr_info.variation_priority')
    variation_display_type = fields.String(attribute='attr_info.variation_display_type')
    group_id = fields.Integer(attribute='attr_info.attribute_group_id')
    group_level1_id = fields.Integer(attribute='attr_info.group_level1_id')
    text_before = fields.String(attribute='attr_info.text_before')
    text_after = fields.String(attribute='attr_info.text_after')
    highlight = fields.Boolean(attribute='attr_info.highlight')


class AttributeGroupDetail(Schema):
    id = fields.Integer()
    name = fields.String()
    priority = fields.Integer()
    parent_id = fields.Integer()
    level = fields.Integer()
    is_flat = fields.Boolean()
    path = fields.String()
    system_group = fields.Boolean()


class AttributeSetDetail(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    has_product = fields.Boolean()
    groups = fields.Nested(AttributeGroupDetail, many=True)
    attributes = fields.Nested(Attribute, many=True)


class GetAttributeSetListParam(ListParamBase, SortableParam):
    query = origin_fields.String()


class GenericAttributeSet(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    created_at = fields.String()
    updated_at = fields.String()


class GetAttributeSetListResponse(ListResponseBase):
    attribute_sets = fields.Nested(GenericAttributeSet(many=True))


class CreateAttributeSetRequestBody(Schema):
    name = fields.String(required=True, allow_none=False, min_len=1, max_len=255)


class CreateAttributeSetResponse(Schema):
    id = fields.Integer()
    name = origin_fields.String()
    code = origin_fields.String()
    created_at = fields.String()
    updated_at = fields.String()


class UpdateAttributeSetRequestBody(Schema):
    class GroupData(Schema):
        class AttributeData(Schema):
            id = fields.Integer(required=True, allow_none=False)
            priority = fields.Integer(required=True, allow_none=False)
            text_before = fields.String(allow_none=True, max_len=255)
            text_after = fields.String(allow_none=True, max_len=255)
            highlight = fields.Boolean(allow_none=True)
            is_displayed = fields.Boolean(allow_none=True)

        temp_id = fields.Integer(required=True)
        name = fields.String(required=True, max_len=255, min_len=1)
        parent_id = fields.Integer(required=True)
        priority = fields.Integer(required=True, allow_none=False)
        is_flat = fields.Boolean(required=True)
        level = fields.Integer(required=True)
        attributes = fields.Nested(AttributeData(many=True), allow_none=True)
        system_group = fields.Boolean(required=True)

    attribute_groups = fields.Nested(GroupData(many=True), required=True)


class UpdateAttributeSetResponse(AttributeSetDetail):
    pass


class AttributeSetConfig(Schema):
    class Attribute(Schema):
        id = fields.Integer()
        value = fields.Integer()

    id = fields.Integer()
    brand_id = fields.Integer()
    attributes = fields.Nested(Attribute(many=True))


class AttributeSetConfigList(Schema):
    config_default_id = fields.Integer()
    optional_list = fields.Nested(AttributeSetConfig(many=True))


class UpdateOrderVariationAttributeRequestBody(Schema):
    ids = fields.List(fields.Integer, required=True, allow_none=False)


class VariationAttribute(Schema):
    attribute_id = fields.Integer()
    is_displayed = fields.Boolean()
    priority = fields.Integer()
    variation_priority = fields.Integer()
    variation_display_type = fields.String()
    group_id = fields.Integer()
    group_level1_id = fields.Integer()
    text_before = fields.String()
    text_after = fields.String()
    highlight = fields.Boolean()


class UpdateOrderVariationAttributeResponse(Schema):
    variation_attributes = fields.Nested(VariationAttribute(many=True))


class CreateVariationAttributeRequestBody(Schema):
    attribute_id = fields.Integer(required=True, allow_none=False)
    variation_display_type = fields.String(required=True, allow_none=False)


class AttribuetSetConfigDetail(Schema):
    def __init__(self, **kwargs):
        """
        Prevent text_before and text_after from being stripped
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.do_strip = False

    object_type = fields.String(allow_none=True)
    object_value = origin_fields.Raw(allow_none=True)  # int or string
    text_before = fields.String(allow_none=True)
    text_after = fields.String(allow_none=True)
    priority = fields.Integer()


class UpdateConfigAttributeSetRequestBody(Schema):
    field_display = fields.String()
    detail = fields.Nested(AttribuetSetConfigDetail(many=True))


class UpdateConfigAttributeSetResponse(Schema):
    attribute_set_configs = fields.Nested(AttribuetSetConfigDetail(many=True))


class GetCommonAttributeSetConfigResponse(Schema):
    class ConfigAttribute(Schema):
        name = fields.String()
        value = fields.String()

    attribute_set_name = fields.String(attribute='attribute_set.name')
    brand_name = fields.String(attribute='brand.name', default=None)
    is_default = fields.Boolean()
    attributes = fields.Nested(ConfigAttribute(many=True))


class UpdateConfigsAttributeSetRequestBody(Schema):
    class ConfigOption(Schema):
        class ConfigOptionAttribute(Schema):
            id = fields.Integer()
            value = fields.Integer()

        id = fields.Integer()
        brand_id = fields.Integer()
        is_deleted = fields.Boolean(missing=0)
        attributes = fields.Nested(ConfigOptionAttribute(many=True))

    config_default_id = fields.Integer(allow_none=True)
    optional_list = fields.Nested(ConfigOption(many=True))


class UpdateConfigsAttributeSetResponse(AttributeSetConfigList):
    pass


class GetDetailAttributeSetConfigParams(Schema):
    field_display = fields.String(missing=None)


class GetDetailAttributeSetConfigResponse(Schema):
    class AttribuetSetConfigDetail(AttribuetSetConfigDetail):
        field_display = fields.String()

    detail = fields.Nested(AttribuetSetConfigDetail(many=True))
