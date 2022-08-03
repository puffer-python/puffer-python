# coding=utf-8

from marshmallow import fields as origin_fields, validate

from catalog.api.attribute_set.schema import AttributeGroupDetail, Attribute
from catalog.api.shipping_type.schema import ShippingTypeSchema
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api import (
    ListParamBase,
    ListResponseBase
)


class ListCategoriesParam(ListParamBase):
    platform_id = origin_fields.Integer(missing=None)
    level = origin_fields.Integer(missing=None)
    query = origin_fields.String(missing=None)
    id = origin_fields.Integer(missing=None)
    codes = origin_fields.String(missing=None)
    ids = fields.StringList(cast_fn=int)
    parent_id = origin_fields.Integer(missing=None)
    is_active = origin_fields.Boolean(missing=None)
    seller_ids = origin_fields.String(missing=None)


class CategoryGeneric(Schema):
    class MasterCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()
        path = fields.String()
        full_path = fields.String()

    class SimpleCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()

    class AttributeSetSchema(Schema):
        id = fields.Integer()
        name = fields.String()

    id = fields.Integer()
    code = fields.String()
    name = fields.String()
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    parent = fields.Nested(SimpleCategory())
    master_category = fields.Nested(MasterCategory())
    root = fields.Nested(SimpleCategory())
    path = fields.String()
    depth = fields.Integer()
    unit_id = fields.Integer()
    is_active = fields.Boolean()
    attribute_set = fields.Nested(AttributeSetSchema)
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()
    master_category_id = fields.Integer()
    shipping_types = fields.Nested(ShippingTypeSchema(many=True))
    seller_id = fields.Integer()
    is_adult = fields.Boolean()


class CategoryGenericForList(Schema):
    class MasterCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()
        path = fields.String()
        full_path = fields.String()

    class SimpleCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()

    class AttributeSetSchema(Schema):
        id = fields.Integer()
        name = fields.String()

    id = fields.Integer()
    code = fields.String()
    name = fields.String()
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    parent = fields.Nested(SimpleCategory())
    master_category = fields.Nested(MasterCategory())
    root = fields.Nested(SimpleCategory())
    path = fields.String()
    depth = fields.Integer()
    unit_id = fields.Integer()
    is_active = fields.Boolean()
    attribute_set = fields.Nested(AttributeSetSchema)
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()
    master_category_id = fields.Integer()
    shipping_types = fields.Nested(ShippingTypeSchema(many=True), attribute='mapping_shipping_types')
    seller_id = fields.Integer()
    is_adult = fields.Boolean()


class CategoryDetail(Schema):
    class SimpleCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()

    class MasterCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()
        path = fields.String()

    class Tax(Schema):
        code = fields.String()
        name = fields.String()

    class AttributeSet(Schema):
        id = fields.Integer()
        name = fields.String()

    class Category(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()

    id = fields.Integer()
    code = fields.String()
    name = fields.String()
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    parent = fields.Nested(SimpleCategory())
    master_category = fields.Nested(MasterCategory())
    root = fields.Nested(SimpleCategory())
    path = fields.String()
    depth = fields.Integer()
    unit_id = fields.Integer()
    is_active = fields.Boolean()
    attribute_set = fields.Nested(AttributeSet(), missing=None)
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()
    shipping_types = fields.Nested(ShippingTypeSchema(many=True))
    has_product = fields.Boolean()
    groups = fields.Nested(AttributeGroupDetail, many=True)
    attributes = fields.Nested(Attribute, many=True)
    is_adult = fields.Boolean(default=False)


class ListCategoriesResponse(ListResponseBase):
    categories = fields.Nested(CategoryGenericForList(many=True))


class CategoryTreeSchema(Schema):
    id = fields.Integer(required=True)
    code = fields.String(required=True, min_len=1)
    name = fields.String(required=True, min_len=1)
    is_adult = fields.Boolean(require=True)
    children = fields.Nested(lambda: CategoryTreeSchema(), many=True,
                             attribute='_children')


class CategoryPostSchema(Schema):
    name = fields.String(required=True, min_len=1, max_len=255)
    code = fields.String(required=True, min_len=1, max_len=255)
    parent_id = fields.Integer(required=True)
    tax_in_code = fields.String(allow_none=True)
    tax_out_code = fields.String(allow_none=True)
    manage_serial = fields.Boolean(required=True)
    auto_generate_serial = fields.Boolean()
    unit_id = fields.Integer(allow_none=True)
    shipping_types = fields.List(fields.Integer, allow_none=True)
    attribute_set_id = fields.Integer(allow_none=True)
    master_category_id = fields.Integer(allow_none=True)
    is_adult = fields.Boolean(missing=False)


class CategoryUpdateSchema(Schema):
    name = fields.String(min_len=1, max_len=255)
    code = fields.String(min_len=1, max_len=255)
    parent_id = fields.Integer()
    tax_in_code = fields.String(allow_none=True)
    tax_out_code = fields.String(allow_none=True)
    attribute_set_id = fields.Integer(allow_none=True)
    unit_id = fields.Integer(allow_none=True)
    auto_generate_serial = fields.Boolean()
    manage_serial = fields.Boolean()
    is_active = fields.Boolean()
    master_category_id = fields.Integer(allow_none=True)
    shipping_types = fields.List(fields.Integer, allow_none=True)
    is_adult = fields.Boolean()


class CategoryCloneMasterCategorySchema(Schema):
    master_category_ids = fields.List(fields.Integer, required=True)
    seller_id = fields.Integer(required=True)


class CategoryRecommendationRequest(Schema):
    name = fields.String(max_len=255, required=True)
    limit = origin_fields.Integer(missing=5, validate=(
        validate.Range(max=100)
    ))


class CategoryBase(Schema):
    name1 = fields.String(required=True, min_len=1, max_len=255)
    eng_name1 = fields.String(max_len=255)
    code1 = fields.String(required=True, min_len=1, max_len=255)
    name2 = fields.String(max_len=255)
    eng_name2 = fields.String(max_len=255)
    code2 = fields.String(max_len=255)
    name3 = fields.String(max_len=255)
    eng_name3 = fields.String(max_len=255)
    code3 = fields.String(max_len=255)


class CategoryPostBulkSchema(Schema):
    categories = fields.List(fields.Nested(CategoryBase))
