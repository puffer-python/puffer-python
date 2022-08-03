import logging

from catalog import celery, producer
from catalog.constants import RAM_QUEUE
from catalog.models import Unit, db
from catalog.biz.unit_upsert import uom_pb2
from catalog.extensions import signals, queue_publisher

__author__ = 'Nam.VH'
_logger = logging.getLogger(__name__)


def to_dict(unit):
    """Transform unit object to dict"""

    if isinstance(unit, Unit):
        return unit.to_dict()

    # if unit is m.AttributeOption's object
    if unit.seller_id == 0 and unit.attribute.code == 'uom':
        return {
            'name': unit.value,

            'code': unit.code,
        }


@signals.on_unit_created
def on_unit_created(unit):
    """
    unit should be sent to central MQ right after being created

    :param unit:
    :return:
    """
    producer.send(connection=db.session,
                  message={
                      "id": unit.id
                  }, ref=str(unit.id), event_key=RAM_QUEUE.RAM_INSERT_UNIT_KEY)


@signals.on_unit_updated
def on_unit_updated(unit):
    """
    unit should be sent to central MQ right after being updated

    :param unit:
    :return:
    """
    producer.send(connection=db.session,
                  message={
                      "id": unit.id
                  }, ref=str(unit.id), event_key=RAM_QUEUE.RAM_UPDATE_UNIT_KEY)


@signals.on_unit_deleted
def on_unit_deleted(unit):
    """
    unit should be sent to central MQ right after being deleted

    :param unit:
    :return:
    """
    publish_unit.delay(to_dict(unit), 'teko.catalog.uom.deleted', headers={'X-code': unit.code})


unit_mapping_key = {
    "code": "code",
    "name": "name",
}


@celery.task()
def publish_unit(unit, routing_key, headers=None):
    publisher = queue_publisher.QueuePublisher()

    message = uom_pb2.UomMessage()

    for key, value in unit_mapping_key.items():
        if unit.get(value) is not None:
            setattr(message, key, unit.get(value))

    setattr(message, 'isActive', 1)
    message = message.SerializeToString()

    publisher.publish_message(message=message, routing_key=routing_key, headers=headers)
