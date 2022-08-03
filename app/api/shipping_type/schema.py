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

__author__ = 'phuong.h'
_logger = logging.getLogger(__name__)


class ShippingTypeSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    is_active = fields.Boolean()
    is_default = fields.Boolean()
    created_by = fields.String()
    updated_by = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class ShippingTypeListParams(ListParamBase):
    name = fields.String()
    code = fields.String()
    query = fields.String()


class ShippingTypeListResponse(ListResponseBase):
    shipping_types = fields.Nested(ShippingTypeSchema(many=True))


class CreateShippingTypeRequest(Schema):
    name = fields.String(min_len=1, max_len=255, required=True)
    code = fields.String(min_len=1, max_len=255, required=True, match='^[A-Z_]+$')


class UpdateShippingTypeRequest(Schema):
    name = fields.String(min_len=1, max_len=255, required=True)
