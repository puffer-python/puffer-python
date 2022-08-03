# coding=utf-8
from google.protobuf import json_format
from marshmallow import fields

from catalog import producer
from catalog import models as m
from catalog.constants import RAM_QUEUE
from catalog.extensions import signals
from catalog.extensions.marshmallow import Schema
from catalog.biz.sellable import sellable_pb2
from catalog.biz.sellable import sellable_update_pb2
from catalog.models import db


class SellableUpdateSchema(Schema):
    sku = fields.String()
    part_number = fields.String()
    barcode = fields.String()
    name = fields.String()
    uom_code = fields.String()
    uom_po_code = fields.String()
    type = fields.String(attribute='product_type', default=None)
    allow_selling_without_stock = fields.Boolean(default=False)
    categ_code = fields.String(attribute='seller_category_code')
    cost_price_calc = fields.Boolean(default=False)
    vat_in_code = fields.String(attribute='tax_in_code')
    warranty_period = fields.Float(attribute='warranty_months')
    warranty_note = fields.String()
    product_brand_code = fields.String(attribute='brand.internal_code')
    days_before_exp_lock = fields.Integer(default=None)
    weight = fields.Integer(default=0)
    length = fields.Integer(default=0)
    width = fields.Integer(default=0)
    height = fields.Integer(default=0)
    seller_id = fields.Integer()
    serial_tracking = fields.Boolean(default=False, attribute='tracking_type')
    auto_generate_serial = fields.Boolean(default=False)
    sellable = fields.Boolean(default=None)
    expiry_tracking = fields.Boolean(default=False)
    expiration_type = fields.Integer()
    seller_sku = fields.String()
    shipping_types = fields.List(fields.String(), attribute='shipping_type_code')
    is_active = fields.Boolean(default=False, attribute='is_active')


class SellableCreateSchema(SellableUpdateSchema):
    sku_id = fields.Integer(attribute='id')


@signals.on_sellable_create
def on_sellable_created(sellable, allow_send_to_srm=True, **kwargs):
    existing_sibling_sku_obj = kwargs.get('existing_sibling_sku_obj')
    if existing_sibling_sku_obj: # publish event AddVariantSkuMsg to Clearance svc
        from catalog.extensions.ram.publisher import add_variant_sku_ram_publisher
        from catalog.extensions.ram.publisher import AddVariantSkuMsg
        add_variant_sku_ram_publisher.publish(AddVariantSkuMsg(
            variant_sku=sellable.sku,
            sibling_sku=existing_sibling_sku_obj.sku,
        ))

    if sellable.is_bundle or not allow_send_to_srm:
        return
    producer.send(message={"routing_key": "teko.catalog.sellable.created", "id": sellable.id},
                  event_key=RAM_QUEUE.RAM_PUSH_PRODUCT_DATA,
                  connection=db.session)


@signals.on_sellable_common_update
def on_sellable_updated(sellable):
    if sellable.is_bundle:
        return
    producer.send(message={"routing_key": "teko.catalog.sellable.updated", "id": sellable.id,
                           "headers": {'X-feid': str(sellable.id)}
                           },
                  event_key=RAM_QUEUE.RAM_PUSH_PRODUCT_DATA,
                  connection=db.session)
