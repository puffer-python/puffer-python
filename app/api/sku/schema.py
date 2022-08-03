# coding=utf-8

from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

__author__ = 'Dung.BV'


class CreateListSku(Schema):
    class Variant(Schema):
        class Sku(Schema):
            id = fields.Integer()
            sku = fields.String()
            seller_sku = fields.String()
            seller_id = fields.Integer()
            uom_code = fields.String()
            uom_name = fields.String()
            uom_ratio = fields.Float()
            name = fields.String()
            need_convert_qty = fields.Integer()
