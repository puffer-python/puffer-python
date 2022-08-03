# coding=utf-8
import logging
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api import (
    ListParamBase,
    ListResponseBase,
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class BrandListRequest(ListParamBase):
    query = fields.String()
    ids = fields.StringList(cast_fn=int, required=False)
    codes = fields.String()
    is_active = fields.Boolean(allow_str=True)
    approved_status = fields.Boolean(allow_str=True)
    has_logo = fields.Boolean(allow_str=True)


class BrandRequest(Schema):
    name = fields.String(required=True, min_len=1, max_len=100)
    code = fields.String(required=True)
    logo = fields.String()
    doc_request = fields.Boolean(required=True)


class BrandSchema(Schema):
    id = fields.Integer()
    internal_code = fields.String()
    code = fields.String()
    name = fields.String()
    is_active = fields.Boolean()
    doc_request = fields.Boolean()
    approved_status = fields.Boolean()
    path = fields.String()
    created_by = fields.String()
    updated_by = fields.String()
    created_at = fields.String()
    updated_at = fields.String()


class BrandListSchema(ListResponseBase):
    brands = fields.Nested(BrandSchema, many=True)


class BrandUpdateRequest(Schema):
    name = fields.String(min_len=1, max_len=100)
    logo = fields.String(allow_none=True)
    doc_request = fields.Boolean()
    is_active = fields.Boolean()


class BrandUpdateImageRequest(Schema):
    code = fields.String(required=True)
    logo = fields.String(required=True)
