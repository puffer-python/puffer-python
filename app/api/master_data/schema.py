# coding=utf-8
import logging

from catalog.extensions.marshmallow import (
    Schema,
    EXCLUDE,
    fields
)
from marshmallow import Schema as OriginalSchema
from catalog.api.product.sellable import schema as sellable_schema

__author__ = 'Nam.VH'
_logger = logging.getLogger(__name__)


class TerminalRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    seller_id = fields.Integer(required=True)
    name = fields.String(min_len=1, required=True)
    code = fields.String(min_len=1, required=True)
    type = fields.String()
    platform = fields.String()
    full_address = fields.String()
    is_active = fields.Boolean(default=False)
    is_requested_approval = fields.Boolean(default=False)
    updated_at = fields.DateTime()


class TerminalGroupSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    name = fields.String(min_len=1, required=True)
    code = fields.String(min_len=1, required=True)
    type = fields.String()
    seller_id = fields.Integer(required=True)
    is_active = fields.Boolean(default=False)


class SellerTerminalGroupSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    seller_id = fields.Integer(required=True)
    terminal_group_id = fields.Integer(required=True)
    is_requested_approval = fields.Boolean(default=False)


class TerminalGroupMappingRequestSchema(OriginalSchema):
    class Meta:
        unknown = EXCLUDE

    class TerminalGroupMapping(OriginalSchema):
        class Terminal(OriginalSchema):
            code = fields.String(required=True)

        class Group(OriginalSchema):
            code = fields.String(required=True)
            type = fields.String(required=True)

        id = fields.Integer(required=True)
        terminal = fields.Nested(Terminal)
        group = fields.Nested(Group)

    op_type = fields.String(required=True)
    terminal_groups = fields.Nested(TerminalGroupMapping, many=True, required=True)


class SellerRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    name = fields.String(min_len=1, required=True)
    code = fields.String(min_len=1, required=True)
    is_auto_generated_sku = fields.Boolean(default=False)
    using_goods_management_modules = fields.Boolean(default=False)
    is_active = fields.Boolean(default=False)
    full_address = fields.String()
    brc_code = fields.String()
    slogan = fields.String()
    tax_id_number = fields.String()
    display_name = fields.String()


class TerminalSchema(Schema):
    id = fields.Integer()
    seller_id = fields.Integer()
    name = fields.String()
    code = fields.String()
    type = fields.String()
    platform = fields.String()
    full_address = fields.String()
    is_active = fields.Boolean()
    is_requested_approval = fields.Boolean()
    updated_at = fields.DateTime()


class SellerTerminalRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    seller_id = fields.Integer(required=True)
    terminal_id = fields.Integer(required=True)
    is_requested_approval = fields.Boolean(default=False)
    is_owner = fields.Boolean(default=False)


class SellerTerminalSchema(Schema):
    id = fields.Integer()
    seller_id = fields.Integer()
    terminal_id = fields.Integer()
    is_requested_approval = fields.Boolean()
    is_owner = fields.Boolean()


class SellingSellerPlatform(Schema):
    id = fields.Integer()
    seller_id = fields.Integer(required=True)
    platform_id = fields.Integer(required=True)
    owner_seller_id = fields.Integer(required=True)
    is_default = fields.Integer()
    created_at = fields.String()
    updated_At = fields.String()


class IdOnlySchema(Schema):
    id = fields.Integer()


class UpdateSrmStatus(Schema):
    code = fields.String(allow_none=True, required=True)


UpdateStatusSrmResponse = sellable_schema.SellableProductSchema
