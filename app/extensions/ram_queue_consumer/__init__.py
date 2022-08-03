import json
import logging

import config

from catalog.biz.category.category import can_create_category_on_srm
from catalog.biz.listing import push_sellable_product_detail
from catalog.extensions.ram_queue_consumer.sellable_product_consummer import ProductDetail
from contextlib import contextmanager

from google.protobuf import json_format
from sqlalchemy.orm import sessionmaker

from catalog import models, producer
from catalog.biz.brand_upsert import brand_pb2
from catalog.biz.category import CategoryMessage, CategorySchema, CategoryUpdateMessage, CategoryUpdateSchema
from catalog.biz.listing import update_product_detail_table, update_product_detail_by_brand, \
    update_product_detail_by_attribute
from catalog.biz.sellable import sellable_update_pb2, sellable_pb2, SellableUpdateSchema, SellableCreateSchema
from catalog.biz.unit_upsert import uom_pb2
from catalog.constants import RAM_QUEUE
from catalog.extensions import queue_publisher
from catalog.extensions.queue_publisher import QueuePublisher
from catalog.extensions.signals import ram_category_created_signal, platform_seller_upsert_created_signal
from catalog.services import seller as seller_service
from catalog.services.seller import get_platform_by_seller_id
from ram.v1_0.consumer.ram_consumer import RamConsumer
from ram.v1_0.stop_retry_exception import StopRetryException
from ram.v1_0.ram_config import DEFAULT_PARENT_KEY

_logger = logging.getLogger(__name__)

# at the module level, the global sessionmaker,
# bound to a specific Engine
Session = sessionmaker(bind=models.db.engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def parse_message_has_id(message):
    try:
        obj = json.loads(message)
    except Exception:
        raise StopRetryException('can not parse message to Json Object')
    if 'id' not in obj:
        raise StopRetryException('the message missing "id" attribute')
    return obj


def _push_message(message, routing_key, headers=None):
    publisher = QueuePublisher()
    publisher.publish_message(
        message=message.SerializeToString(),
        routing_key=routing_key,
        headers=headers
    )


def _get_category_seller_ids(message, owner_seller_id):
    if message.get('seller_id'):
        return [message.get('seller_id')]
    else:
        platform_ids = get_platform_by_seller_id(owner_seller_id)
        return seller_service.get_seller_default_on_platform(platform_ids)


def _process_category_upsert(session, object_message, event='created'):
    category = session.query(models.Category).get(object_message["id"])
    if not category:
        raise StopRetryException(f'can not find record with id= {object_message["id"]} in categories table')
    headers = None
    if event == 'updated':
        routing_key = 'teko.catalog.category.updated'
        message = CategoryUpdateMessage()
        data = CategoryUpdateSchema().dump(category)
        headers = {'X-feid': str(category.id)}
    else:

        routing_key = 'teko.catalog.category.created'
        message = CategoryMessage()
        data = CategorySchema().dump(category)
    messages = []
    seller_ids = _get_category_seller_ids(object_message, category.seller_id)
    for seller_id in seller_ids:
        for key, value in data.items():
            if value is not None:
                setattr(message, key, value)
        setattr(message, 'sellerId', seller_id)
        _push_message(
            message=message,
            routing_key=routing_key,
            headers=headers
        )
        messages.append(message)
    return messages


def process_create_category(message):
    obj = parse_message_has_id(message)
    with session_scope() as session:
        _process_category_upsert(session, obj)


def process_update_category(message):
    obj = parse_message_has_id(message)
    with session_scope() as session:
        _process_category_upsert(session, obj, 'updated')


def build_unit_proto_message(ram_message):
    obj = parse_message_has_id(ram_message)
    with session_scope() as session:
        unit = session.query(models.Unit).get(obj["id"])
        if not unit:
            raise StopRetryException(f'can not find record with id= {obj["id"]} in units table')

        message = uom_pb2.UomMessage()
        message.code = unit.code or ''
        message.name = unit.name or ''
        message.sellerId = unit.seller_id or 0
        message.displayName = unit.display_name or ''
        message.isActive = 1
        return message.SerializeToString(), unit.code


def process_create_unit(message):
    proto_message, _ = build_unit_proto_message(message)
    QueuePublisher().publish_message(
        message=proto_message,
        routing_key='teko.catalog.uom.created'
    )


def process_update_unit(message):
    proto_message, unit_code = build_unit_proto_message(message)
    QueuePublisher().publish_message(
        message=proto_message,
        routing_key='teko.catalog.uom.updated',
        headers={'X-code': unit_code}
    )


def build_brand_proto_message(session, ram_message):
    obj = parse_message_has_id(ram_message)
    brand = session.query(models.Brand).get(obj["id"])
    if not brand:
        raise StopRetryException(f'can not find record with id= {obj["id"]} in brands table')

    message = brand_pb2.BrandMessage()
    message.code = brand.internal_code or ''
    message.name = brand.name or ''
    message.isActive = brand.is_active or 1
    return message.SerializeToString(), brand


def process_create_brand(message):
    with session_scope() as session:
        proto_message, _ = build_brand_proto_message(session, message)
        QueuePublisher().publish_message(
            message=proto_message,
            routing_key='teko.catalog.brand.created'
        )


def process_update_brand(message):
    with session_scope() as session:
        proto_message, brand = build_brand_proto_message(session, message)
        QueuePublisher().publish_message(
            message=proto_message,
            routing_key='teko.catalog.brand.updated',
            headers={'X-code': brand.internal_code}
        )
        # Sync product details
        updated_by = brand.updated_by or 'system'
        update_product_detail_by_brand(brand.id, updated_by=updated_by)
        select_skus = f'''select id, "{DEFAULT_PARENT_KEY}", "{RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL_V2}", 1,
                        "CREATED", JSON_OBJECT("sku", sku, "updated_by", "{updated_by}"), now()
                        FROM sellable_products where brand_id = {brand.id}'''
        producer.send_by_select(session, select_skus)


def process_update_attribute(message):
    # Comment
    # CATALOGUE - 1445
    pass
    # data = json.loads(message)
    # updated_by = data.get('updated_by') or 'system'
    # attribute_id = data.get('attribute_id')
    # attribute_option_id = data.get('attribute_option_id')
    # update_product_detail_by_attribute(attribute_id, option_id=attribute_option_id, updated_by=updated_by)
    # with session_scope() as session:
    #     if attribute_option_id:
    #         option_condition = f' = {attribute_option_id}'
    #     else:
    #         option_condition = ' IS NOT NULL'
    #     select_skus = f'''SELECT id, "{DEFAULT_PARENT_KEY}", "{RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL_V2}", 1,
    #                     "CREATED", JSON_OBJECT("sku", sku, "updated_by", "{updated_by}"), now()
    #                         FROM sellable_products WHERE exists
    #                         (SELECT va.id FROM variant_attribute va
    #                          WHERE va.variant_id = sellable_products.variant_id
    #                         AND va.attribute_id = {attribute_id} AND va.value {option_condition})'''
    #     producer.send_by_select(session, select_skus)


def process_push_product_data(message):
    obj = parse_message_has_id(message)
    with session_scope() as session:
        sellable_product = session.query(models.SellableProduct).get(obj.get('id'))
        sellable_product.set_seller_category_code(session)
        routing_key = obj.get('routing_key', 'teko.catalog.sellable.updated')
        if routing_key == 'teko.catalog.sellable.created':
            message_scheme = sellable_pb2.SellableMessage()
            data = SellableCreateSchema().dump(sellable_product)
        else:
            data = SellableUpdateSchema().dump(sellable_product)
            message_scheme = sellable_update_pb2.SellableUpdateMessage()
        if data.get('categCode'):
            message = json_format.ParseDict(data, message_scheme, ignore_unknown_fields=True)
            publisher = queue_publisher.QueuePublisher()
            publisher.publish_message(
                message=message.SerializeToString(),
                routing_key=routing_key,
                headers=obj.get('headers', {})
            )


def process_update_product_detail(message):
    with session_scope() as session:
        data = json.loads(message)
        update_product_detail_table(
            skus=data.get('sku'),
            updated_by=data.get('updated_by')
        )
        product_detail = session.query(models.ProductDetail).filter(
            models.ProductDetail.sku == data.get('sku')
        ).first()
        push_sellable_product_detail(product_data=product_detail.data, ppm_listed_price=data.get('ppm_listed_price'))


def __get_product_detail_v2(session, message):
    data = json.loads(message)
    sku = data.get('sku')
    updated_by = data.get('updated_by')
    product_detail = ProductDetail(session)
    return product_detail.init_product_detail_v2(sku, updated_by)


def process_update_product_detail_v2(message):
    with session_scope() as session:
        sku_detail = __get_product_detail_v2(session, message)
        if sku_detail:
            exist = session.query(models.ProductDetailsV2).filter(
                models.ProductDetailsV2.sku == sku_detail.get('sku')).first()
            if exist:
                for k, v in sku_detail.items():
                    setattr(exist, k, v)
            else:
                sku_detail['created_by'] = sku_detail['updated_by']
                model = models.ProductDetailsV2(**sku_detail)
                session.add(model)


def __get_platform_categories_query(session, owner_seller_id):
    return session.query(models.Category).filter(models.Category.seller_id == owner_seller_id,
                                                 models.Category.is_active.is_(True)) \
        .order_by(models.Category.depth,
                  models.Category.path)


def process_platform_seller_upsert(message):
    with session_scope() as session:
        data = json.loads(message)
        owner_seller_id = data.get('owner_seller_id')
        seller_id = data.get('seller_id')
        root_cat = __get_platform_categories_query(session, owner_seller_id).first()
        if can_create_category_on_srm(root_cat, seller_id=seller_id):
            platform_categories = __get_platform_categories_query(session, owner_seller_id).all()
            # It needs to send all categories for all services to get this data.
            # However, it can be failed on SRM because we create it before
            for category in platform_categories:
                ram_category_created_signal.send({'id': category.id, 'seller_id': seller_id})
        else:
            data['after_seconds'] = config.SYNC_CATEGORY_TO_SRM_DELAY_TIME
            platform_seller_upsert_created_signal.send(data)


def run_default_consumer():
    consumer = RamConsumer(map_event_key_with_handler={
        RAM_QUEUE.RAM_INSERT_CATEGORY_KEY: process_create_category,
        RAM_QUEUE.RAM_UPDATE_CATEGORY_KEY: process_update_category,
        RAM_QUEUE.RAM_INSERT_UNIT_KEY: process_create_unit,
        RAM_QUEUE.RAM_UPDATE_UNIT_KEY: process_update_unit,
        RAM_QUEUE.RAM_INSERT_BRAND_KEY: process_create_brand,
        RAM_QUEUE.RAM_UPDATE_BRAND_KEY: process_update_brand,
        RAM_QUEUE.RAM_UPDATE_ATTRIBUTE_KEY: process_update_attribute,
        RAM_QUEUE.RAM_PLATFORM_SELLER_UPSERT_KEY: process_platform_seller_upsert,
    })

    consumer.start()


def run_push_push_product_data_consumer():
    consumer = RamConsumer(map_event_key_with_handler={
        RAM_QUEUE.RAM_PUSH_PRODUCT_DATA: process_push_product_data
    })

    consumer.start()


def run_update_product_detail_consumer():
    consumer = RamConsumer(map_event_key_with_handler={
        RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL: process_update_product_detail
    })

    consumer.start()


def run_update_product_detail_v2_consumer():
    consumer = RamConsumer(map_event_key_with_handler={
        RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL_V2: process_update_product_detail_v2
    })

    consumer.start()
