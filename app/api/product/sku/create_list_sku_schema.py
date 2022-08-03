# coding=utf-8
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

from .schema import Barcode


class AttributeRequest(Schema):
    id = fields.Integer(required=True)
    value = fields.String(min_len=0, max_len=255, allow_none=True)


class ImageRequest(Schema):
    url = fields.String(max_len=500)
    alt_text = fields.String(max_len=255)
    allow_display = fields.Boolean(allow_none=True)


class SkuRequest(Schema):
    sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$')
    seller_sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$')
    name = fields.String(max_len=255)
    barcode = fields.List(Barcode())
    barcodes = fields.List(Barcode())
    part_number = fields.String(max_len=255)
    tracking_type = fields.Boolean(allow_none=True)
    days_before_exp_lock = fields.Integer(max_val=1000)
    expiry_tracking = fields.Boolean(allow_none=True)
    expiration_type = fields.Integer(allow_none=True, restricted_values=[1, 2])
    product_type = fields.String(max_len=255, default='consu')
    images = fields.Nested(ImageRequest(many=True))
    shipping_type_id = fields.Integer(allow_none=True)
    detailed_description = fields.String(max_len=70000)
    description = fields.String(max_len=500)
    display_name = fields.String(max_len=255)
    meta_title = fields.String(max_len=255)
    meta_description = fields.String(max_len=255)
    meta_keyword = fields.String(max_len=255)
    url_key = fields.String(max_len=255)
    editing_status_code = fields.String()


class VariantRequest(Schema):
    variant_id = fields.Integer(allow_none=True)
    uom_id = fields.Integer(allow_none=True)
    uom_ratio = fields.PositiveFloat(default=1.0, missing=1.0, allow_none=True)
    attributes = fields.Nested(AttributeRequest(many=True), allow_none=True)
    sku = fields.Nested(SkuRequest(allow_none=True))


class CreateListSkuRequest(Schema):
    seller_id = fields.Integer(required=True)
    created_by = fields.String(required=True)
    product_id = fields.Integer(allow_none=True)
    name = fields.String(data_key='product_name', min_len=1, max_len=255)
    master_category_id = fields.Integer(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    category_ids = fields.List(fields.Integer, required=False, allow_none=True)
    attribute_set_id = fields.Integer(allow_none=True, required=False)
    brand_id = fields.Integer(allow_none=True)
    provider_id = fields.Integer(allow_none=True)
    model = fields.String(max_len=255)
    tax_in_code = fields.String(allow_none=True)
    warranty_months = fields.Integer(min_val=0, max_val=9999)
    warranty_note = fields.String(max_len=500)
    detailed_description = fields.String(max_len=70000)
    description = fields.String(max_len=500)
    variants = fields.Nested(VariantRequest(many=True))


class VariantResponse(Schema):
    variant_id = fields.Integer(allow_none=True)
    sku_id = fields.Integer(allow_none=True)
    sku = fields.String(allow_none=True)
    seller_sku = fields.String(allow_none=True)


class CreateListSkuResponse(Schema):
    product_id = fields.Integer(allow_none=True)
    variants = fields.Nested(VariantResponse(many=True))
