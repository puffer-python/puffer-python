import logging

from catalog import models, producer
from catalog.constants import RAM_QUEUE
from catalog.extensions import signals

__author__ = 'Quang.LM'

_logger = logging.getLogger(__name__)


#

@signals.on_attribute_updated
def on_attribute_updated(attribute):
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_UPDATE_ATTRIBUTE_KEY, message={
            'attribute_id': attribute.id,
        }, ref=attribute.id)


@signals.on_attribute_option_updated
def on_attribute_option_updated(attribute_option):
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_UPDATE_ATTRIBUTE_KEY, message={
            'attribute_id': attribute_option.attribute_id, 'attribute_option_id': attribute_option.id
        }, ref=attribute_option.id)
