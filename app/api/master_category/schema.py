# coding=utf-8
import logging

from catalog.api import (
    ListParamBase,
    ListResponseBase,
)
from marshmallow import fields as original_fields
from catalog.extensions.marshmallow import (
    Schema,
    fields
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class MasterCategorySchema(Schema):
    class SimpleiMasterCategory(Schema):
        id = fields.Integer()
        name = fields.String()
        code = fields.String()

    class AttributeSetSchema(Schema):
        id = fields.Integer()
        name = fields.String()

    id = fields.Integer(required=True)
    name = fields.String()
    code = fields.String()
    depth = fields.Integer()
    path = fields.String()
    image = fields.String()
    is_active = fields.Boolean()
    root = fields.Nested(SimpleiMasterCategory())
    parent = fields.Nested(SimpleiMasterCategory())
    attribute_set = fields.Nested(AttributeSetSchema())
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()


class MasterCategoryListParams(ListParamBase):
    is_active = original_fields.Boolean()
    level = fields.Integer(min_val=1, max_val=9, strict=False, missing=None)
    parent_id = fields.Integer(min_val=1, strict=False, missing=None)
    query = fields.String(missing=None)
    id = fields.Integer(strict=False)


class MasterCategoryListResponse(ListResponseBase):
    master_categories = fields.Nested(MasterCategorySchema(many=True))


class CreateMasterCategoryRequestBody(Schema):
    name = fields.String(min_len=1, max_len=255, required=True)
    code = fields.String(required=True, match=r'^[a-zA-Z0-9-_\.]{1,255}$')
    image = fields.String(min_len=1)
    parent_id = fields.Integer(missing=0)
    tax_in_code = fields.String()
    tax_out_code = fields.String()
    attribute_set_id = fields.Integer(allow_none=True)
    manage_serial = fields.Boolean()
    auto_generate_serial = fields.Boolean()


class UpdatePositionRequest(Schema):
    parent_id = fields.Integer(required=True)
    left_node_id = fields.Integer(allow_none=True, default=0)


class MasterCategoryTreeSchema(Schema):
    id = fields.Integer(required=True)
    code = fields.String(required=True, min_len=1)
    name = fields.String(required=True, min_len=1)
    depth = fields.Integer()
    children = fields.Nested(lambda: MasterCategoryTreeSchema(), many=True,
                             attribute='_children')


class UpdateMasterCategoryRequest(CreateMasterCategoryRequestBody):
    parent_id = fields.Integer()
    name = fields.String(min_len=1, max_len=255, required=False)
    code = fields.String(required=False, match=r'^[a-zA-Z0-9-_\.]{1,255}$')
    is_active = fields.Boolean()


class CategoryRecommendationResponse(Schema):
    class AttributeSetSchema(Schema):
        id = fields.Integer()
        name = fields.String()

    id = fields.Integer()
    name = fields.String()
    path = fields.String()
    full_path = fields.String()
    attribute_set = fields.Nested(AttributeSetSchema())
