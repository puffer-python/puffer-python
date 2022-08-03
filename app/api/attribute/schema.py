# coding=utf-8

from marshmallow import (
    fields as original_fields,
    validate
)
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api import (
    ListParamBase,
    ListResponseBase,
)


class Unit(Schema):
    id = fields.Integer()
    code = fields.String()
    name = fields.String()


class AttributeOption(Schema):
    id = fields.Integer()
    code = fields.String()
    value = fields.String()


class Attribute(Schema):
    id = fields.Integer()
    name = fields.String()
    display_name = fields.String()
    value_type = fields.String()
    code = fields.String()
    options = fields.Nested(AttributeOption(many=True))
    unit_id = fields.Integer()
    description = fields.String()
    is_required = fields.Boolean()
    is_searchable = fields.Boolean()
    is_filterable = fields.Boolean()
    is_comparable = fields.Boolean()
    is_system = fields.Boolean(allow_num=True, default=False)


class AttributeListResponse(ListResponseBase):
    attributes = fields.Nested(Attribute(many=True))


class AttributeListParam(ListParamBase):
    query = fields.String()
    value_type = fields.String()
    description = fields.String()
    is_required = fields.Boolean(allow_str=True)
    is_searchable = fields.Boolean(allow_str=True)
    is_filterable = fields.Boolean(allow_str=True)
    is_comparable = fields.Boolean(allow_str=True)


class AttributeCreateData(Schema):
    name = fields.String(min_len=1, max_len=255, required=True, allow_none=False)
    display_name = fields.String(min_len=1, max_len=255, required=True, allow_none=False)
    value_type = fields.String(min_len=1, max_len=255, required=True, allow_none=False)
    code = fields.String(required=True, allow_none=False, min_len=1, max_len=255)
    description = fields.String(min_len=0, max_len=255, allow_none=False)
    unit_id = fields.Integer(allow_none=False)
    is_required = fields.Boolean(missing=False)
    is_searchable = fields.Boolean(missing=False)
    is_filterable = fields.Boolean(missing=False)
    is_comparable = fields.Boolean(missing=False)
    is_system = fields.Boolean(default=False, allow_num=True, required=False)


class AttributeUpdateData(AttributeCreateData):
    unit_id = fields.Integer(allow_none=True)


class AttributeOptionCreateRequest(Schema):
    value = fields.String(required=True, min_len=1, max_len=100, allow_none=False)
    code = fields.String(min_len=1, max_len=100, allow_none=False, match=r'^[a-zA-Z0-9\-]+$')


class AttributeOptionUpdateRequest(Schema):
    value = fields.Raw(min_len=1, max_len=100, allow_none=False)


class AttributeOptionGetListQuery(ListParamBase):
    keyword = fields.String(min_len=0)
    ids = fields.StringList(cast_fn=int)
    codes = fields.StringList()


class AttributeOptionGetListResponse(ListResponseBase):
    options = fields.Nested(AttributeOption, many=True)


class GetOptionsOfAttributeRequestParam(Schema):
    ids = fields.StringList(cast_fn=int, required=True, allow_none=False)


class GetOptionsOfAttribute(Schema):
    attribute_id = fields.Integer()
    options = fields.Nested(AttributeOption(many=True))
