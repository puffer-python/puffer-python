# coding=utf-8
from catalog.extensions.marshmallow import (
    Schema,
    fields
)
from marshmallow import validate
from .schema import Barcode


class ImageRequest(Schema):
    url = fields.String(required=True, max_len=500)
    alt_text = fields.String(required=False, max_len=255)
    allow_display = fields.Boolean(default=True, missing=True, required=False)


class CreateSkuRequest(Schema):
    sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$')
    seller_sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$')
    name = fields.String(max_len=255)
    barcode = fields.List(Barcode())
    barcodes = fields.List(Barcode())
    part_number = fields.String(max_len=255)
    tracking_type = fields.Boolean()
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer(restricted_values=[1, 2])
    days_before_expLock = fields.Integer(strict=True, min_val=0, max_val=10000)
    product_type = fields.String(validate=validate.OneOf(['product', 'consu']))
    images = fields.Nested(ImageRequest(many=True))
    shipping_type_id = fields.Integer(allow_none=True)
    detailed_description = fields.String(max_len=70000)
    description = fields.String(max_len=500)
    display_name = fields.String(max_len=255)
    meta_title = fields.String(max_len=255)
    meta_description = fields.String(max_len=255)
    meta_keyword = fields.String(max_len=255)
    url_key = fields.String(max_len=255)


class BarcodeRequest(Schema):
    barcode = fields.String(required=True, max_len=30, match='^[a-zA-Z0-9.\-]*$', min_len=1)
    source = fields.String(required=True, max_len=255, min_len=1)


class UpdateSkuRequest(Schema):
    barcodes = fields.List(fields.Nested(BarcodeRequest), required=True, validate=validate.Length(min=1))


class MoveSkuRequest(Schema):
    sku = fields.String(required=True, max_len=20)


class MoveSkusRequest(Schema):
    skus = fields.List(fields.String(max_len=20), required=True)
    target_product_id = fields.Integer(required=True)
    seller_id = fields.Integer(required=True)
