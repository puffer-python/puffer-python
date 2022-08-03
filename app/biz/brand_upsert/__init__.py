import logging

from catalog import models, producer
from catalog.biz.brand_upsert import brand_pb2
from catalog.constants import RAM_QUEUE
from catalog.extensions import signals
from catalog.extensions.marshmallow import (
    Schema,
    fields,
)

__author__ = 'Nam.VH'

_logger = logging.getLogger(__name__)


class BrandSchema(Schema):
    name = fields.String()
    is_active = fields.Boolean()
    code = fields.String(attribute='internal_code')


@signals.on_brand_created
def on_brand_created(brand):
    """
    Brand should be sent to central MQ right after being created

    :param brand:
    :return:
    """
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_INSERT_BRAND_KEY, message={
                      'id': brand.id
                  }, ref=brand.id)


@signals.on_brand_updated
def on_brand_updated(brand):
    """
    Brand should be sent to central MQ right after being updated

    :param brand:
    :return:
    """
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_UPDATE_BRAND_KEY, message={
                      'id': brand.id
                  }, ref=brand.id)
