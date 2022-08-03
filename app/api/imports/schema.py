# coding=utf-8

from marshmallow import INCLUDE, validate
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog.api import (
    ListParamBase,
    ListResponseBase,
    SortableParam,
)

DATE_FMT = '%d/%m/%Y'


class FileImportHistoryListParam(ListParamBase, SortableParam):
    created_by = fields.String()
    status = fields.StringList()
    type = fields.StringList()
    start_at = fields.Date(DATE_FMT)
    end_at = fields.Date(DATE_FMT)


class FileImportHistory(Schema):
    id = fields.Integer()
    name = fields.String()
    created_by = fields.String()
    created_at = fields.String()
    status = fields.String()
    total_row = fields.Integer()
    total_row_success = fields.Integer()
    path = fields.String()
    success_path = fields.String()
    note = fields.String()
    seller_id = fields.Integer()
    type = fields.String()
    attribute_set_id = fields.Integer()


class FileImportParam(Schema):
    class Meta:
        unknown = INCLUDE

    type = fields.String(required=True)
    attribute_set_id = fields.String()
    platform_id = fields.Integer()


class FileImportHistoryList(ListResponseBase):
    histories = fields.Nested(FileImportHistory(many=True))


class ImportCreateProductBasicInfoParams(Schema):
    attribute_set_id = fields.Integer(required=True)


class RetryImport(Schema):
    id = fields.Integer(required=True)
    status = fields.String(required=True)
    message = fields.String(required=True)


class ImportHistoryItemRequest(Schema):
    id = fields.Integer()
    data = fields.Raw()

class RetryImportRequestBody(Schema):
    saveOnly = fields.Boolean(required=True)
    items = fields.Nested(ImportHistoryItemRequest(many=True))


class ImportHistoryItemParam(ListParamBase):
    status = fields.String(allow_none=True, validate=validate.OneOf(
        ['success', 'failure', 'fatal']
    ))
    query = fields.String(allow_none=True)

class ImportHistoryItem(Schema):
    id = fields.Integer()
    name = fields.String()
    message = fields.String()
    status = fields.String()
    updated_at = fields.String()
    updated_by = fields.String()
    data = fields.Raw()


class ImportHistoryItemList(ListResponseBase):
    items = fields.Nested(ImportHistoryItem(many=True))
    column_config = fields.Raw()
