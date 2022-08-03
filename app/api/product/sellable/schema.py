# coding=utf-8
import logging

from catalog import constants
from catalog.api.product.variant import schema
from catalog.api.shipping_type.schema import ShippingTypeSchema
from catalog.extensions.marshmallow import Schema, fields
from catalog import constants
from catalog.api import ListResponseBase, ListParamBase

__author__ = 'Kien'

from catalog.extensions.marshmallow.validators import VietnameseWithSpecialCharacters

_logger = logging.getLogger(__name__)


class BarcodeWithSource(Schema):
    barcode = fields.String(required=True, max_len=30, match='^[a-zA-Z0-9.\-]*$')
    source = fields.String(required=False, max_len=255)


class SellableProductRequest(Schema):
    variant_id = fields.Integer(required=True)
    sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$',
                        allow_none=False)
    seller_sku = fields.String(max_len=20, match='^[a-zA-Z0-9.\-_/]*$',
                               allow_none=False)
    provider_id = fields.Integer(allow_none=False)
    barcode = fields.String(max_len=30, match='^[a-zA-Z0-9.\-]*$',
                            allow_none=False)
    barcodes = fields.List(fields.Nested(BarcodeWithSource))
    supplier_sale_price = fields.Integer(min_val=0, max_val=1000000000,
                                         allow_none=True)
    part_number = fields.String(max_len=255, allow_none=False)
    allow_selling_without_stock = fields.Boolean(default=False, allow_none=True)
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean(default=False, missing=False, allow_none=True)
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer(restricted_values=[1, 2])
    days_before_exp_lock = fields.Integer(strict=True, min_val=0, max_val=10000)
    shipping_types = fields.List(fields.Integer, allow_none=True)
    short_description = fields.String(max_len=500, allow_none=True)
    description = fields.String(allow_none=True)


class SellableProductsRequest(Schema):
    product_id = fields.Integer(required=True)
    sellable_products = fields.Nested(SellableProductRequest, many=True,
                                      required=True)


class BrandSchema(Schema):
    id = fields.Integer()
    name = fields.String()


class AttributeSetSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()


class CategorySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    full_path = fields.String()
    path = fields.String()


class MasterCategorySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    full_path = fields.String()
    path = fields.String()


class StatusSchema(Schema):
    code = fields.String()
    name = fields.String()
    config = fields.Raw()


class SellableProductSchema(Schema):
    id = fields.Integer()
    sku = fields.String()
    seller_sku = fields.String()
    product_id = fields.Integer()
    provider_id = fields.Integer()
    product_name = fields.String(attribute='product.name', missing=None,
                                 default=None)
    type = fields.String(attribute='product_type', missing=None,
                         default=None)
    variant_id = fields.Integer()
    name = fields.String(missing=None, default=None)
    image = fields.String(attribute='avatar_url', missing=None,
                          default=None)
    barcode = fields.String()
    warranty_months = fields.Integer()
    warranty_note = fields.String()
    editing_status = fields.Nested(StatusSchema, missing=None, default=None)
    selling_status = fields.Nested(StatusSchema, missing=None, default=None)
    label = fields.String()
    is_bundle = fields.Boolean()
    seller_id = fields.Integer()
    supplier_sale_price = fields.Integer()
    part_number = fields.String()
    brand = fields.Nested(BrandSchema, missing=None, default=None)
    category = fields.Nested(CategorySchema, missing=None, default=None)
    master_category = fields.Nested(MasterCategorySchema, missing=None, default=None)
    attribute_set = fields.Nested(AttributeSetSchema, missing=None,
                                  default=None)
    model = fields.String()
    unit_id = fields.Integer()
    unit_po_id = fields.Integer()
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    allow_selling_without_stock = fields.Boolean(default=False, )
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer()
    days_before_exp_lock = fields.Integer()
    created_at = fields.String()
    updated_at = fields.String()
    created_by = fields.String()
    updated_by = fields.String()
    description = fields.String(attribute='terminal_seo.short_description')
    detailed_description = fields.String(attribute='terminal_seo.description')
    shipping_types = fields.Nested(ShippingTypeSchema(many=True))


class SellableProductCommonSchema(SellableProductSchema):
    shipping_property = fields.String()


class SellableProductAttribute(schema.VariantAttribute):
    id = fields.Integer(attribute='attribute.id')
    name = fields.String(attribute='attribute.name')
    code = fields.String(attribute='attribute.code')
    value_type = fields.String(attribute='attribute.value_type')


class SellableProductTerminalSellerDataSchema(Schema):
    terminal_type = fields.String(allow_none=True)
    terminal_codes = fields.Raw(required=True, allow_none=False)


class SellableProductTerminalSellerSchema(Schema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_none = False

    apply_seller_id = fields.Integer()
    terminals = fields.List(
        fields.Nested(SellableProductTerminalSellerDataSchema),
        required=True
    )


class SellableProductTerminalSchema(Schema):
    skus = fields.List(fields.String, required=True)
    seller_terminals = fields.List(
        fields.Nested(SellableProductTerminalSellerSchema),
        required=True
    )


class SellableProductTerminal(Schema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_none = False

    apply_seller_id = fields.Integer()
    terminals = fields.Nested(SellableProductTerminalSellerDataSchema, many=True)


class SellableProductDetail(Schema):
    common = fields.Nested(SellableProductCommonSchema)
    images = fields.Nested(schema.VariantImage, many=True)
    specs = fields.Nested(SellableProductAttribute, many=True)
    terminals = fields.Nested(SellableProductTerminal, many=True)
    terminal_groups = fields.List(fields.String())
    uom = fields.Raw()


class SellableProductListRequest(Schema):
    ids = fields.StringList(cast_fn=int, allow_none=False)
    seller_ids = fields.StringList(allow_none=False, cast_fn=int)
    skus = fields.StringList(allow_none=False)
    keyword = fields.StringList(allow_none=False)
    category = fields.String(allow_none=False)
    category_ids = fields.String(allow_none=False)
    provider_ids = fields.StringList(cast_fn=int)
    master_category = fields.String(allow_none=False)
    brand = fields.String(allow_none=False)
    brand_ids = fields.String(allow_none=False)
    attribute_set = fields.String(allow_none=False)
    selling_status = fields.String(allow_none=False)
    editing_status = fields.String(allow_none=False)
    terminal = fields.String(allow_none=False)
    terminal_group = fields.String(allow_none=False)
    is_bundle = fields.Boolean(allow_str=True, default=False)
    page = fields.Integer(strict=False, allow_none=False, missing=1, min_val=1)
    page_size = fields.Integer(strict=False, allow_none=False,
                               missing=10, min_val=1)
    export = fields.Integer(strict=False, missing=0, allow_none=False)


class SellableProductGeneralInfo(Schema):
    class Category(Schema):
        id = fields.Integer()
        code = fields.String()
        name = fields.String()

    id = fields.Integer()
    is_allow_create_variant = fields.Boolean()
    name = fields.String(missing=None)
    product_id = fields.Integer(missing=None)
    product_name = fields.String(attribute='product.name', missing=None)
    provider_id = fields.Integer()
    sku = fields.String()
    seller_sku = fields.String()
    barcode = fields.String()
    image = fields.String(attribute='avatar_url', missing=None)
    category = fields.Nested(Category, missing=None, default=None)
    brand = fields.Nested(BrandSchema, missing=None, default=None)
    selling_status = fields.Nested(StatusSchema)
    editing_status = fields.Nested(StatusSchema)
    seller_id = fields.Integer()
    uom_code = fields.String()
    uom_name = fields.String()


class SellableProductInventorySyncInfo(Schema):
    id = fields.Integer()
    sku = fields.String()
    seller_sku = fields.String()
    seller_id = fields.Integer()
    uom_code = fields.String()
    uom_name = fields.String()
    uom_ratio = fields.Float()
    name = fields.String()
    need_convert_qty = fields.Integer()


class SellableProductList(Schema):
    current_page = fields.Integer()
    page_size = fields.Integer()
    totalRecords = fields.Integer()
    skus = fields.Nested(SellableProductGeneralInfo, many=True)


class UpdateEditingStatusRequestBody(Schema):
    ids = fields.List(fields.Integer(), many=True)
    skus = fields.List(fields.String(), many=True)
    status = fields.String(min_len=1, required=True)
    comment = fields.String(max_len=255)


class UpdateEditingStatusResponse(Schema):
    ids = fields.List(fields.Integer(), many=True, required=True)
    skus = fields.List(fields.String(), many=True, required=True)


class GetSkusBySellerSku(ListParamBase):
    seller_skus = fields.StringList()
    skus = fields.StringList()
    restrict_convert_qty = fields.Number()
    seller_id = fields.Number()


class GetSkusBySellerSkuResponse(ListResponseBase):
    skus = fields.Nested(SellableProductInventorySyncInfo, many=True)


class UpdateCommonRequestBody(Schema):
    name = fields.String(max_len=255, min_len=1, allow_none=False)
    category_id = fields.Integer(allow_none=False)
    provider_id = fields.Integer(allow_none=False)
    unit_id = fields.Integer(allow_none=False)
    master_category_id = fields.Integer(allow_none=True)
    brand_id = fields.Integer(allow_none=False)
    model = fields.String(allow_none=True, max_len=255)
    warranty_months = fields.Integer(allow_none=False, min_val=0, max_val=9999)
    warranty_note = fields.String(allow_none=True, max_len=255)
    tax_in_code = fields.String(allow_none=False)
    tax_out_code = fields.String(allow_none=True)
    type = fields.String(allow_none=False)
    description = fields.String(allow_none=True, max_len=500)
    detailed_description = fields.String(allow_none=True, max_len=70000)
    barcode = fields.String(max_len=30, match=r'^[a-zA-Z0-9.\-]*$',
                            allow_none=True)
    part_number = fields.String(allow_none=True, max_len=255)
    allow_selling_without_stock = fields.Boolean(allow_none=True, default=True)
    manage_serial = fields.Boolean(allow_none=False)
    auto_generate_serial = fields.Boolean(allow_none=False)
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer(restricted_values=[1, 2])
    days_before_exp_lock = fields.Integer(strict=True, min_val=0, max_val=10000)


class UpdateCommonRequest(UpdateCommonRequestBody):
    shipping_types = fields.List(fields.Integer, allow_none=True)


class UpdateCommonResponse(UpdateCommonRequestBody):
    editing_status_code = fields.String()
    shipping_types = fields.Nested(ShippingTypeSchema(many=True))


class SellableTerminalProductListRequest(Schema):
    keyword = fields.String(allow_none=False)
    category = fields.String(allow_none=False)
    master_category = fields.String(allow_none=False)
    brand = fields.String(allow_none=False)
    seller = fields.String(allow_none=False)
    selling_status = fields.String(allow_none=False)
    terminal = fields.String(allow_none=False)
    on_off_status = fields.String(required=True)
    is_bundle = fields.Boolean(allow_str=True)
    page = fields.Integer(strict=False, allow_none=False, missing=1,
                          min_val=1, max_val=constants.SQL_MAX_INTVAL)
    page_size = fields.Integer(strict=False, allow_none=False, missing=10,
                               min_val=1)


class BundleSchema(Schema):
    id = fields.Integer()
    sku = fields.String()
    seller_sku = fields.String()
    name = fields.String()
    editing_status = fields.Nested(StatusSchema)
    quantity = fields.Integer()
    priority = fields.Integer()
    selling_status = fields.Nested(StatusSchema)
    allow_selling_without_stock = fields.Boolean()


class ItemBundleInfo(Schema):
    id = fields.Integer(required=True, allow_none=False)
    quantity = fields.Integer(required=True, min_val=1, max_val=1000,
                              allow_none=False)


class UpdateSellableBundleRequestBody(Schema):
    items = fields.Nested(ItemBundleInfo(many=True), required=True, allow_none=False)


class UpdateSellableBundleResponse(UpdateSellableBundleRequestBody):
    pass


class GetSellableBundleResponseBody(Schema):
    items = fields.Nested(BundleSchema(many=True))


class SEOInfo(Schema):
    display_name = fields.String(
        max_len=255,
        allow_none=True,
        required=False,
        validate=[VietnameseWithSpecialCharacters(match='^[a-zA-Z0-9 .,&_()/-]*$')]
    )
    meta_title = fields.String(allow_none=True, required=False, max_len=255)
    meta_description = fields.String(allow_none=True, required=False, max_len=255)
    meta_keyword = fields.String(allow_none=True, required=False, max_len=255)
    description = fields.String(allow_none=True, required=False)
    url_key = fields.String(allow_none=False, required=True, min_len=1,
                            validate=[VietnameseWithSpecialCharacters(match='^[a-zA-Z0-9-]*$')])
    short_description = fields.String(allow_none=True, required=False, max_len=500)


class GetSEOInfoRequest(Schema):
    terminal_codes = fields.String(max_len=45, allow_none=True) # deprecated


class GetSEOInfoResponse(Schema):
    display_name = fields.String(default=None)
    meta_title = fields.String(default=None)
    meta_description = fields.String(default=None)
    meta_keyword = fields.String(default=None)
    description = fields.String(default=None)
    short_description = fields.String(default=None)
    url_key = fields.String(default=None)


class PutSEOInfo(Schema):
    terminal_codes = fields.List(fields.String(min_len=1, max_len=45), required=False) # deprecated
    seo_info = fields.Nested(nested=SEOInfo, required=True, allow_none=False)


class SellableJsonUpsertSchema(Schema):
    skus = fields.List(fields.String())


class SellableProductTerminalGroup(Schema):
    sellable_products = fields.List(fields.Integer())
    terminal_groups = fields.List(fields.String(min_len=1, max_len=255))


class SellableTerminalGroupProductListRequest(Schema):
    keyword = fields.StringList(allow_none=False)
    category = fields.String(allow_none=False)
    master_category = fields.String(allow_none=False)
    brand = fields.String(allow_none=False)
    selling_status = fields.String(allow_none=False)
    terminal_group = fields.String(allow_none=False)
    is_bundle = fields.Boolean(allow_str=True)
    page = fields.Integer(strict=False, allow_none=False, missing=1,
                          min_val=1, max_val=constants.SQL_MAX_INTVAL)
    page_size = fields.Integer(strict=False, allow_none=False, missing=10,
                               min_val=1)


class ApplyShippingType(Schema):
    ids = fields.List(fields.Integer, allow_none=True)
    action = fields.String(allow_none=True)


class ApplyFilterCondition(Schema):
    category_id = fields.Integer(allow_none=True)


class ApplyData(Schema):
    shipping_type = fields.Nested(ApplyShippingType())


class ApplySellableProductsRequest(Schema):
    data = fields.Nested(ApplyData(), required=True)
    filter_condition = fields.Nested(ApplyFilterCondition(), )


class UpdateCommonV2RequestBody(Schema):
    name = fields.String(max_len=255, min_len=1, allow_none=False)
    category_id = fields.Integer(allow_none=False)
    provider_id = fields.Integer(allow_none=False)
    master_category_id = fields.Integer(allow_none=True)
    brand_id = fields.Integer(allow_none=False)
    model = fields.String(allow_none=True, max_len=255)
    warranty_months = fields.Integer(allow_none=False, min_val=0, max_val=9999)
    warranty_note = fields.String(allow_none=True, max_len=255)
    tax_in_code = fields.String(allow_none=False)
    tax_out_code = fields.String(allow_none=True)
    type = fields.String(allow_none=False)
    description = fields.String(allow_none=True, max_len=500)
    detailed_description = fields.String(allow_none=True, max_len=70000)
    barcode = fields.String(max_len=30, match=r'^[a-zA-Z0-9.\-]*$',
                            allow_none=True)
    part_number = fields.String(allow_none=True, max_len=255)
    allow_selling_without_stock = fields.Boolean(allow_none=True, default=False)
    manage_serial = fields.Boolean(allow_none=False)
    auto_generate_serial = fields.Boolean(allow_none=False)
    expiry_tracking = fields.Boolean()
    expiration_type = fields.Integer(restricted_values=[1, 2])
    days_before_exp_lock = fields.Integer(strict=True, min_val=0, max_val=10000)
    shipping_types = fields.List(fields.Integer(), allow_none=True)
