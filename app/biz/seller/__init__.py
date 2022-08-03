# coding=utf-8
from catalog import producer, models
from catalog.constants import RAM_QUEUE
from catalog.extensions.signals import on_platform_seller_upsert_created
from catalog.utils import safe_cast


@on_platform_seller_upsert_created
def category_updated_handler(data):
    seller_id = data.get('seller_id')
    platform_id = data.get('platform_id')
    after_seconds = data.pop('after_seconds', None)
    delay = 0
    if after_seconds:
        delay = safe_cast(after_seconds, int, 0) * 1000
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_PLATFORM_SELLER_UPSERT_KEY, message=data, ref=f'{seller_id}_{platform_id}',
                  delay_milliseconds=delay)
