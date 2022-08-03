# coding=utf-8

from catalog.extensions.marshmallow import (
    Schema,
    fields,
)
from catalog import celery, producer, models
from catalog.extensions.queue_publisher import QueuePublisher
from catalog.extensions.signals import (
    on_category_created,
    on_category_updated, on_ram_category_created, on_ram_category_updated,
)
from catalog import models as m
from .category_pb2 import CategoryMessage
from .category_update_pb2 import CategoryUpdateMessage
from .category import create_seller_categories_from_master_categories, create_categories_on_SRM
from ...constants import RAM_QUEUE


class CategoryUpdateSchema(Schema):
    name = fields.String()
    code = fields.String()
    parent = fields.Integer(attribute='parent_id')
    seller_id = fields.Integer()
    is_active = fields.Boolean()
    tax_in_code = fields.String()
    path = fields.String()
    tax_out_code = fields.String()
    income_account = fields.String(missing=None)
    internal_income_account = fields.String(missing=None)
    tracking = fields.String()
    stock_valuation_account = fields.String(missing=None)
    sale_branch = fields.String(missing=None)
    expense_account = fields.String(missing=None)
    return_account = fields.String(missing=None)


class CategorySchema(CategoryUpdateSchema):
    fe_id = fields.Integer(attribute='id')


@on_category_created
def category_created_handler(category):
    publish_category.delay(category.id, 'teko.catalog.category.created')


@on_category_updated
def category_updated_handler(category):
    publish_category.delay(category.id, 'teko.catalog.category.updated',
                           {'X-feid': str(category.id)})


@celery.task()
def publish_category(category_id, routing_key, headers=None):
    publisher = QueuePublisher()
    category = m.Category.query.get(category_id)
    if routing_key == 'teko.catalog.category.created':
        message = CategoryMessage()
        data = CategorySchema().dump(category)
    else:
        message = CategoryUpdateMessage()
        data = CategoryUpdateSchema().dump(category)
    for key, value in data.items():
        if value is not None:
            setattr(message, key, value)
    publisher.publish_message(
        message=message.SerializeToString(),
        routing_key=routing_key,
        headers=headers
    )


@on_ram_category_created
def ram_category_created_handler(category_entity):
    category_id = category_entity.get('id')
    if category_entity.get('seller_id'):
        data = {
            'id': category_id,
            'seller_id': category_entity.get('seller_id')
        }
    else:
        data = {
            'id': category_id
        }
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_INSERT_CATEGORY_KEY, message=data, ref=str(category_id))


@on_ram_category_updated
def ram_category_updated_handler(category_entity):
    producer.send(connection=models.db.session,
                  event_key=RAM_QUEUE.RAM_UPDATE_CATEGORY_KEY, message={
            'id': category_entity.id
        }, ref=str(category_entity.id))
