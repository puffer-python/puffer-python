# coding=utf-8

from marshmallow import ValidationError
from marshmallow import fields as fields_original

from catalog.api import (
    ListResponseBase,
    ListParamBase,
    SortableParam,
)
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)


class VariantAttributeValue(fields.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if value is None:
            return
        value_type = type(value)
        if value_type not in (int, float, str, list):
            raise ValidationError('Kiểu dữ liệu không hợp lệ')
        if value_type is list:
            for val in value:
                if not isinstance(val, int):
                    raise ValidationError('Kiểu dữ liệu không hợp lệ')

    def _deserialize(self, value, attr, obj, **kwargs):
        return value

    def _serialize(self, value_or_callable, attr, data, **kwargs):
        if callable(value_or_callable):
            value = value_or_callable()
        else:
            value = value_or_callable
        if type(value) in (str, int, float):
            return value

        def map_option(option):
            return option.id

        if isinstance(value, list):
            return list(map(map_option, value))
        return map_option(value)


class VariantAttribute(Schema):
    id = fields.Integer(attribute='attribute_id')
    value = VariantAttributeValue(attribute='get_value')


class GenericVariant(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    name = fields.String()
    code = fields.String()
    url_key = fields.String()
    editing_status_code = fields.String()
    model = fields.String()
    is_generated_sku = fields.Boolean(attribute='number_of_sku')
    uom_ratio = fields.Float()
    uom_code = fields.String(attribute='unit.code')
    uom_name = fields.String(attribute='unit.value')
    created_at = fields.String()
    updated_at = fields.String()
    created_by = fields.String(allow_none=True)
    updated_by = fields.String(allow_none=True)


class Variant(GenericVariant):
    class VariantAttribute(Schema):
        id = fields.Integer()
        value = fields.Integer()

    attributes = fields.Nested(VariantAttribute(many=True))


class CreateVariantsBodyRequest(Schema):
    class Variant(Schema):
        class VariantAttribute(Schema):
            id = fields.Integer(required=True)
            value = fields.NotNegativeFloat(required=True)

        name = fields.String()
        attributes = fields.Nested(VariantAttribute(many=True),
                                   required=True)

    product_id = fields.Integer(required=True)
    variants = fields.Nested(Variant(many=True), required=False)


class CreateVariantsResponse(Schema):
    product_id = fields.Integer()
    variants = fields.Nested(Variant(many=True))


class UpdateVariantsData(Schema):
    class VariantData(Schema):
        class Image(Schema):
            url = fields.String(required=True, max_len=500)
            alt_text = fields.String(required=False, max_len=255)
            allow_display = fields.Boolean(default=True, required=False)

        id = fields.Integer(required=True)
        images = fields.Nested(Image(many=True), required=True)

    variants = fields.Nested(VariantData(many=True), required=True)


class VariantImage(Schema):
    id = fields.Integer()
    url = fields.String()
    status = fields.Boolean()
    alt_text = fields.String(attribute='label', default='')
    allow_display = fields.Boolean(attribute='is_displayed')
    priority = fields.Integer()


class UpdateVariantsResponse(Schema):
    class VariantData(Schema):
        class UomResponse(Schema):
            base = fields.Integer()
            ratio = fields.Float()

        id = fields.Integer()
        images = fields.Nested(VariantImage(many=True))
        uom = fields.Nested(UomResponse)

    variants = fields.Nested(VariantData(many=True))


class CreateVariantAttributeRequest(Schema):
    class Variant(Schema):
        class VariantAttribute(Schema):
            id = fields.Integer(required=True)
            value = VariantAttributeValue(required=True, allow_none=True)

        id = fields.Integer(required=True)
        attributes = fields.Nested(VariantAttribute(many=True), required=True)

    variants = fields.Nested(Variant(many=True), required=True)


class CreateVariantAttributeResponse(Schema):
    id = fields.Integer()
    attributes = fields.Nested(VariantAttribute(many=True))


class GetVariantListParam(ListParamBase, SortableParam):
    product_id = fields_original.Integer()
    query = fields_original.String()
    editing_status_code = fields_original.String()


class GetVariantListResponse(ListResponseBase):
    class VariantWithImage(GenericVariant):
        images = fields.Nested(VariantImage(many=True))
        variation_attributes = fields.Nested(VariantAttribute(many=True))

    variants = fields.Nested(VariantWithImage(many=True))


class GetVariantAttributeListParam(Schema):
    variant_ids = fields.StringList(cast_fn=int, required=True, allow_none=False)


class GetVariantAttributeListResponse(Schema):
    variants = fields.Nested(CreateVariantAttributeResponse(many=True))


class CreateExternalImageResponse(Schema):
    request_id = fields.String()


class CreateExternalImageParams(Schema):
    images = fields.List(fields.String, required=True)
