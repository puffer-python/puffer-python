# coding=utf-8
from marshmallow import ValidationError

from catalog.api.extra.schema import EditingStatus
from catalog.api.product.sellable.schema import AttributeSetSchema, CategorySchema
from catalog.api.product.variant.schema import VariantImage
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.extensions.exceptions import BadRequestException


class BarcodeWithSource(Schema):
    barcode = fields.String(required=True, max_len=30, match='^[a-zA-Z0-9.\-]*$')
    source = fields.String(required=False, max_len=255)


class Barcode(fields.Raw):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            barcode = {
                'barcode': value
            }
        else:
            barcode = value
        try:
            BarcodeWithSource().load(barcode)
        except ValidationError:
            raise BadRequestException(message='barcodes không hợp lệ')
        return barcode


class BrandSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    logo = fields.String(attribute='path', missing=None)


class BarcodeSchema(Schema):
    barcode = fields.String()
    source = fields.String()
    is_default = fields.Boolean()


class InternalCategorySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    full_path = fields.String(attribute="ext_full_path_data")
    path = fields.String()


class SkuInfoResponse(Schema):
    id = fields.Integer(attribute='response_id')
    sku = fields.String(attribute='response_sku')
    seller_sku = fields.String(attribute='response_seller_sku')
    name = fields.String(missing=None)
    url_key = fields.String(attribute='ext_product_variant_data.url_key')
    images = fields.Nested(nested=VariantImage(many=True), attribute='ext_variant_images_data')
    editing_status = fields.Nested(EditingStatus(), attribute='ext_editing_status_data')
    seller_id = fields.Integer()
    provider_id = fields.Integer()
    product_id = fields.Integer(missing=None)
    product_name = fields.String(attribute='ext_product_data.name', missing=None)
    warranty_months = fields.Integer()
    warranty_note = fields.String()
    attribute_set = fields.Nested(AttributeSetSchema(), attribute='ext_attribute_set_data')
    model = fields.String(attribute='ext_product_data.model')
    tax_in_code = fields.String()
    product_type = fields.String()
    variant_id = fields.Integer()
    uom_name = fields.String()
    uom_code = fields.String()
    uom_ratio = fields.Float()
    category = fields.Nested(CategorySchema(), missing=None, default=None, attribute='platform_category')
    default_category = fields.Nested(CategorySchema(), missing=None, default=None)
    master_category = fields.Nested(InternalCategorySchema(), missing=None, default=None, attribute='ext_master_category_data')
    brand = fields.Nested(BrandSchema(), missing=None, attribute='ext_brand_data')
    barcode = fields.List(fields.String(), attribute='barcodes')
    barcodes = fields.Nested(BarcodeSchema(many=True), attribute='barcodes_with_source')
    part_number = fields.String()
    shipping_type_id = fields.Integer(attribute="ext_shipping_type_data.shipping_type_id")
    tracking_type = fields.Boolean()
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer()
    days_before_exp_lock = fields.Integer()


class GetListSkuResponse(Schema):
    page = fields.Integer()
    page_size = fields.Integer()
    totalRecords = fields.Integer()
    products = fields.Nested(SkuInfoResponse, many=True)


class GetListSkuRequest(Schema):
    product_ids = fields.StringList(cast_fn=int, ignore_cast_error=True, min_len=1)
    variant_ids = fields.StringList(cast_fn=int, ignore_cast_error=True, min_len=1)
    seller_ids = fields.StringList(cast_fn=int, ignore_cast_error=True, min_len=1)
    platform_id = fields.Integer(strict=False)
    skus = fields.StringList()
    seller_skus = fields.StringList()
    keyword = fields.StringList()
    attribute_set_ids = fields.String()
    category_ids = fields.String()
    master_category_ids = fields.String()
    provider_ids = fields.StringList(cast_fn=int, ignore_cast_error=True, min_len=1)
    barcodes = fields.StringList()
    brand_ids = fields.String()
    models = fields.StringList()
    editing_status_codes = fields.StringList()
    page = fields.Integer(strict=False, missing=1, min_val=1)
    page_size = fields.Integer(strict=False, missing=10, min_val=1)


class CreateSubSKuResponse(Schema):
    sku = fields.String()
