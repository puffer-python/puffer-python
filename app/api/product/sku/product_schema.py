# coding=utf-8
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)


class CreateProductRequest(Schema):
    provider_id = fields.Integer(allow_none=True)
    seller_id = fields.Integer(required=True)
    name = fields.String(required=True)
    category_id = fields.Integer(required=False)
    category_ids = fields.List(fields.Integer, required=False, allow_none=True)
    brand_id = fields.Integer(required=True)
    attribute_set_id = fields.Integer(required=False, allow_none=True)
    tax_in_code = fields.String(required=True)
