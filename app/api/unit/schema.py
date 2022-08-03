# coding=utf-8
import logging

from catalog import constants
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UnitRequest(Schema):
    name = fields.String(required=True, min_len=1, max_len=255)
    code = fields.String(required=True, min_len=1, max_len=30)
    display_name = fields.String(max_len=255)


class UnitSchema(Schema):
    id = fields.Integer()
    code = fields.String()
    name = fields.String()
    display_name = fields.String()
    seller_id = fields.Integer()


class UnitUpdateRequest(Schema):
    name = fields.String(min_len=1, max_len=255)
    display_name = fields.String(max_len=255)


class UnitGetListRequest(Schema):
    query = fields.String()
    page = fields.Integer(strict=False, allow_none=False, missing=1,
                          min_val=1, max_val=constants.SQL_MAX_INTVAL)
    page_size = fields.Integer(strict=False, allow_none=False, missing=10,
                               min_val=1, max_val=constants.MAX_PAGE_SIZE_INTERNAL)


class UnitGetListResponse(Schema):
    current_page = fields.Integer()
    page_size = fields.Integer()
    total_records = fields.Integer()
    units = fields.Nested(UnitSchema, many=True)
