# coding=utf-8
from catalog import constants
from catalog.api.category import schema as category_schema
from catalog.api.master_category import schema as master_category_schema
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)


class ProductCreateRequestBody(Schema):
    name = fields.String(min_len=1, max_len=255, required=True)
    is_bundle = fields.Boolean(required=True)
    master_category_id = fields.Integer(allow_none=False)
    category_id = fields.Integer(missing=None)
    category_code = fields.String(missing=None)
    unit_id = fields.Integer(missing=None)
    unit_code = fields.String(missing=None)
    attribute_set_id = fields.Integer(required=True)
    brand_id = fields.Integer(missing=None)
    brand_code = fields.String(missing=None)
    type = fields.String(required=True)
    model = fields.String(max_len=255, allow_none=False)
    tax_in_code = fields.String(allow_none=False)
    tax_out_code = fields.String(allow_none=True, required=False)
    warranty_months = fields.Integer(min_val=0, max_val=9999, required=True)
    warranty_note = fields.String(max_len=255, allow_none=False)
    detailed_description = fields.String(max_len=70000, allow_none=False)
    description = fields.String(max_len=500, allow_none=False)


class ProductUpdateRequestBody(Schema):
    name = fields.String(min_len=1, max_len=255, allow_none=False)
    category_id = fields.Integer(allow_none=False)
    master_category_id = fields.Integer(allow_none=True)
    brand_id = fields.Integer(allow_none=False)
    type = fields.String(min_len=1, max_len=30, allow_none=False)
    model = fields.String(max_len=255, allow_none=True)
    unit_id = fields.Integer(allow_none=False)
    tax_in_code = fields.String(max_len=10, allow_none=False)
    tax_out_code = fields.String(max_len=10, allow_none=True)
    warranty_months = fields.Integer(min_val=0, max_val=9999, allow_none=False)
    warranty_note = fields.String(max_len=255, allow_none=True)
    detailed_description = fields.String(max_len=70000, allow_none=True)
    description = fields.String(max_len=500, allow_none=True)


class ProductGetRequestParams(Schema):
    brand_ids = fields.StringList(allow_none=False)
    keyword = fields.String(allow_none=False)
    models = fields.StringList(allow_none=False)
    seller_id = fields.Integer(strict=False, allow_none=False)
    page = fields.Integer(strict=False, allow_none=False, missing=1, min_val=1)
    page_size = fields.Integer(strict=False, allow_none=False,
                               missing=10, min_val=1, max_val=constants.MAX_PAGE_SIZE_INTERNAL)


class Attribute(Schema):
    attribute_id = fields.Integer(attribute='attribute_id')
    attribute_name = fields.String(attribute='attribute.display_name')
    attribute_option_id = fields.Integer(attribute='attribute_option.id')
    attribute_option_value = fields.String(attribute='attribute_option_value')


class Variant(Schema):
    variant_id = fields.Integer(attribute='variant_id')
    sku = fields.String(attribute='sku')
    seller_sku = fields.String(attribute='seller_sku')
    seller_id = fields.Integer(attribute='seller_id')
    seller_category_id = fields.Integer(attribute='category_id')
    seller_category_full_path_name = fields.String(attribute='category.full_path')
    variant_attributes = fields.Nested(Attribute(many=True), attribute='product_variant.variation_attributes')


class Product(Schema):
    id = fields.Integer(allow_none=False)
    name = fields.String(allow_none=False, attribute='name')
    model = fields.String(allow_none=False, attribute='model')
    brand_id = fields.Integer(allow_none=False, attribute='brand.id')
    brand_name = fields.String(allow_none=False, attribute='brand.name')
    variants = fields.Nested(Variant(many=True), attribute='sellable_products')


class ProductGetListResponse(Schema):
    products = fields.Nested(Product(many=True))
    current_page = fields.Integer()
    page_size = fields.Integer()
    total_records = fields.Integer()


class GenericProduct(Schema):
    class Brand(Schema):
        id = fields.Integer()
        name = fields.String()

    class AttributeSet(Schema):
        id = fields.Integer()
        name = fields.String()

    id = fields.Integer()
    spu = fields.String()
    name = fields.String(min_len=1, max_len=265, required=True)
    is_bundle = fields.Boolean()
    master_category = fields.Nested(master_category_schema.MasterCategorySchema())
    category = fields.Nested(category_schema.CategoryGeneric())
    attribute_set = fields.Nested(AttributeSet())
    brand = fields.Nested(Brand())
    model = fields.String(max_len=255)
    unit_id = fields.Integer(required=True)
    unit_po_id = fields.Integer()
    tax_in_code = fields.String(required=True)
    tax_out_code = fields.String(required=False)
    warranty_months = fields.Integer(min_val=0, required=True, strict=True)
    warranty_note = fields.String(max_len=255)
    detailed_description = fields.String()
    description = fields.String(max_len=500)
    type = fields.String()
    editing_status_code = fields.String()
    url_key = fields.String()
    updated_at = fields.String()
    created_at = fields.String()
    created_by = fields.String()
    updated_by = fields.String()


class ProductHistoryBasic(Schema):
    id = fields.Integer()
    sku = fields.String()
    old_data = fields.String()
    new_data = fields.String(required=True)
    updated_at = fields.String()
    created_at = fields.String()
    updated_by = fields.String()


class ProductHistory(Schema):
    histories = fields.Nested(ProductHistoryBasic, many=True)


class ProductCreateResponse(GenericProduct):
    pass
