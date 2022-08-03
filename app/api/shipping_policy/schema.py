# coding=utf-8
import logging

from catalog.api import ListParamBase
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class ShippingPolicyListRequest(ListParamBase):
    name = fields.String(max_len=255)
    provider_ids = fields.String()
    is_active = fields.Boolean(allow_str=True, allow_num=True)
    category_ids = fields.String()
    shipping_type = fields.String(match='^(all|near|bulky)$')


class ShippingPolicyCreateRequest(Schema):
    def __init__(self, **kwargs):
        super().__init__(allow_none=False, **kwargs)

    name = fields.String(required=True, max_len=255)
    provider_ids = fields.List(fields.Integer, required=True, allow_duplicate=False)
    is_active = fields.Boolean()
    category_ids = fields.List(fields.Integer, required=True, allow_duplicate=False)
    shipping_type = fields.String(match='^(all|near|bulky)$', required=True)


class CategorySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    code = fields.String()
    depth = fields.Integer()


class ProviderField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return list(set(each.provider_id for each in value))

    def _deserialize(self, value, attr, data, **kwargs):
        return list(set(each.provider_id for each in value))


class ShippingPolicySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    provider_ids = ProviderField(attribute='providers')
    shipping_type = fields.String(attribute='shipping_type_name')
    categories = fields.Nested(CategorySchema, many=True)
    is_active = fields.Boolean()


class ShippingPolicyListSchema(Schema):
    page = fields.Integer()
    page_size = fields.Integer()
    total_records = fields.Integer()
    policies = fields.Nested(ShippingPolicySchema, many=True)


class ShippingPolicyUpdateRequest(Schema):
    def __init__(self, **kwargs):
        super().__init__(allow_none=False, **kwargs)

    name = fields.String(max_len=255)
    provider_ids = fields.List(fields.Integer, allow_duplicate=False)
    is_active = fields.Boolean()
    category_ids = fields.List(fields.Integer, allow_duplicate=False)
    shipping_type = fields.String(match='^(all|near|bulky)$')


class ShippingPolicyUpdateResponse(Schema):
    def __init__(self, **kwargs):
        super().__init__(allow_none=False, **kwargs)

    name = fields.String(max_len=255)
    provider_ids = fields.List(fields.Integer, allow_duplicate=False)
    is_active = fields.Boolean()
    categories = fields.Nested(CategorySchema, many=True)
    shipping_type = fields.String(match='^(all|near|bulky)$')
