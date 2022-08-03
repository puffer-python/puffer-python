# coding=utf-8
from catalog.extensions.marshmallow import (
    Schema,
    fields
)


class AttributeRequest(Schema):
    id = fields.Integer(required=True)
    value = fields.String(allow_none=True, min_len=0, max_len=255)


class CreateVariantRequest(Schema):
    variant_id = fields.Integer(allow_none=True)
    uom_id = fields.Integer(required=True)
    uom_ratio = fields.PositiveFloat(default=1.0, missing=1.0, allow_none=True)
    attributes = fields.Nested(AttributeRequest(many=True), allow_none=True)
