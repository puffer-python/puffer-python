# coding=utf-8
import logging
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class ManufactureResponse(Schema):
    id = fields.Integer()
    code = fields.String(attribute='display_code')
    name = fields.String(attribute='value')
