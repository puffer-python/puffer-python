#coding=utf-8

from catalog.extensions.marshmallow import (
    Schema,
    fields,
)


class Tax(Schema):
    code = fields.String()
    amount = fields.Float()
    label = fields.String()
