# coding=utf-8
# pylint: disable=E0401,E1133,E1111,E0213
import json

from google.protobuf import json_format
from sqlalchemy import text

from catalog import models as m
from catalog.biz.listing import CatalogProductMessage
from catalog.biz.sellable import SellableCreateSchema
from catalog.biz.sellable.sellable_pb2 import SellableMessage
from catalog.extensions import queue_publisher
from catalog.extensions.signals import on_sub_sku_created


def push_sub_sku_detail(sku):
    product_detail = m.ProductDetail.query.filter(m.ProductDetail.sku == sku).first()
    if product_detail:
        product_data = product_detail.data
        routing_key = 'teko.catalog.product.upsert'
        data = json.loads(product_data)
        data.update({
            'url_key': data.get('url')
        })
        message_publish = json_format.ParseDict(data, CatalogProductMessage(), ignore_unknown_fields=True)
        message = json_format.ParseDict(data, message_publish, ignore_unknown_fields=True)
        publisher = queue_publisher.QueuePublisher()
        publisher.publish_message(
            message=message.SerializeToString(),
            routing_key=routing_key
        )


def push_sub_sku(id):
    routing_key = 'teko.catalog.sellable.created'
    sub_sku = m.SellableProductSubSku.query.get(id)
    message_scheme = SellableMessage()
    data = SellableCreateSchema().dump(sub_sku.sellable_product)
    data['skuId'] = sub_sku.id
    data['sku'] = sub_sku.sub_sku
    data['sellerSku'] = sub_sku.sub_sku
    data['barcode'] = ""
    message = json_format.ParseDict(data, message_scheme, ignore_unknown_fields=True)
    publisher = queue_publisher.QueuePublisher()
    publisher.publish_message(
        message=message.SerializeToString(),
        routing_key=routing_key
    )


@on_sub_sku_created
def select_and_insert_sub_sku_json(sub_sku, updated_by=None):
    """
    :param sub_sku:
    :param updated_by
    :return:
    """
    product_detail = m.ProductDetail.query.filter(
        m.ProductDetail.sku == sub_sku.sellable_product.sku).first()
    if product_detail:
        insert_into_values_on_duplicate = text(""" 
        insert into product_details (sku, data, updated_by, created_at, updated_at)
        values (:sku, JSON_SET(:product_json, '$.parent_sku', :parentSku, '$.sku', :sku, '$.id', :id, '$.seller_sku', :sku), :updated_by, now(), now())
        ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = now(), updated_by = :updated_by
        """)
        values = [{
            'parentSku': sub_sku.sellable_product.sku,
            'sku': sub_sku.sub_sku,
            'product_json': product_detail.data,
            'updated_by': updated_by,
            'id': sub_sku.id,
        }]

        m.db.engine.execute(insert_into_values_on_duplicate, *values)
        m.db.session.commit()
        push_sub_sku(sub_sku.id)
        push_sub_sku_detail(sub_sku.sub_sku)
