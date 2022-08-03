# coding=utf-8
import logging

from catalog.api import (
    ListParamBase,
    ListResponseBase,
)
from catalog.extensions.marshmallow import (
    Schema,
    fields
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class SaleCategorySchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String()
    code = fields.String()
    parent_id = fields.Integer()
    depth = fields.Integer()
    path = fields.String()
    priority = fields.Integer()
    image = fields.String()
    is_active = fields.Boolean()


class SaleCategoryListParams(ListParamBase):
    level = fields.Integer(min_val=1, max_val=9, strict=False, missing=None)
    parent_id = fields.Integer(min_val=1, strict=False, missing=None)
    query = fields.String(missing=None)


class SaleCategoryListResponse(ListResponseBase):
    sale_categories = fields.Nested(SaleCategorySchema(many=True))


class SaleCategoryRequest(Schema):
    name = fields.String(min_len=1, max_len=255, required=True)
    code = fields.String(min_len=1, max_len=255, required=True)
    image = fields.String(allow_none=True)
    is_active = fields.Boolean(required=True)
    parent_id = fields.Integer()
    products = fields.List(fields.Integer())


class UpdatePositionRequest(Schema):
    parent_id = fields.Integer(required=True)
    left_node_id = fields.Integer(allow_none=True, default=0)


class SaleCategoryTreeSchema(Schema):
    id = fields.Integer(required=True)
    code = fields.String(required=True, min_len=1)
    name = fields.String(required=True, min_len=1)
    children = fields.Nested(lambda: SaleCategoryTreeSchema(), many=True)


class UpdateSaleCategoryRequest(Schema):
    name = fields.String(min_len=1, allow_none=False)
    code = fields.String(min_len=1, allow_none=False)
    image = fields.String(allow_none=True)
    is_active = fields.Boolean()
