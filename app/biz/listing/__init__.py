# coding=utf-8
import json
import logging

from flask_login import current_user
from google.protobuf import json_format
from sqlalchemy.orm import load_only

from catalog.extensions import signals
from catalog import models as m, producer, models
from catalog.utils import sql_functions
from .catalog_products_pb2 import CatalogProductMessage

__author__ = 'Kien.HT'

from ...constants import RAM_QUEUE
from ...extensions.queue_publisher import QueuePublisher

_logger = logging.getLogger(__name__)


def update_product_detail_table(skus, updated_by='system'):
    sql_functions.select_and_insert_json(
        sellable_sku=skus,
        updated_by=updated_by
    )

    return


def update_product_detail_by_brand(brand_id, updated_by='system'):
    sql_functions.update_by_brand(brand_id, updated_by=updated_by)


def update_product_detail_by_attribute(attribute_id, option_id=None, updated_by='system'):
    sql_functions.update_by_attribute(attribute_id, option_id=option_id, updated_by=updated_by)


def add_ppm_info(data):
    fe_id = data.get('id')
    price_info = models.SellableProductPrice.query.filter(
        models.SellableProductPrice.sellable_product_id == fe_id
    ).first()
    if price_info:
        selling_status = price_info.selling_status == 1
        selling_price = price_info.selling_price
        terminal_group_ids = json.loads(price_info.terminal_group_ids) if price_info.terminal_group_ids else []
        data.update({
            'selling_status': selling_status,
            'selling_price': selling_price,
            'terminal_group_ids': terminal_group_ids,
            'listed_price': selling_price,
            'tax_out_code': price_info.tax_out_code
        })
    return data


def push_sellable_product_detail(product_data, **kwargs):
    """
    Push the product detail to the connector
    Used in the ram events
    Parameters:
    - sku (--text): This is a sku of the system

    :rtype None
    """
    data = json.loads(product_data)
    data.update({
        'url_key': data.get('url')
    })
    if kwargs.get('ppm_listed_price'):
        data = add_ppm_info(data)
    message_publish = json_format.ParseDict(data, CatalogProductMessage(), ignore_unknown_fields=True)
    publisher = QueuePublisher()
    publisher.publish_message(message_publish.SerializeToString(), 'teko.catalog.product.upsert')


@signals.on_sellable_create
@signals.on_sellable_update
@signals.on_sellable_update_seo_info
def update_product_detail(sellable, allow_update_product_detail=True, **kwargs):
    if not allow_update_product_detail:
        return

    sellable_product_skus = [item.sku for item in m.SellableProduct.query.filter(
        m.SellableProduct.product_id == sellable.product_id
    ).options(
        load_only('sku')
    ).all()]

    updated_by = sellable.updated_by or kwargs.get('created_by') or getattr(current_user, 'email', '')
    ppm_listed_price = kwargs.get('ppm_listed_price')
    for sku in sellable_product_skus:
        producer.send(message={"sku": sku, "updated_by": updated_by, "ppm_listed_price": ppm_listed_price},
                      event_key=RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL,
                      connection=models.db.session)
        producer.send(message={"sku": sku, "updated_by": updated_by},
                      event_key=RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL_V2,
                      connection=models.db.session)
