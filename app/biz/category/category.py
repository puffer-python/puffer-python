import logging
import requests
from google.protobuf import json_format
from sqlalchemy import text, or_

import config
from catalog import celery, models
from catalog.biz.sellable import SellableUpdateSchema, sellable_update_pb2
from catalog.extensions import signals, queue_publisher
from catalog.models import db
from catalog.services.categories import CategoryService

_logger = logging.getLogger(__name__)


@signals.on_clone_master_category_request
def on_update_product_terminal_groups_imported(params):
    create_seller_categories_from_master_categories.delay(**params)


@celery.task(queue='clone_master_categories')
def create_seller_categories_from_master_categories(master_category_ids, seller_id, **kwargs):
    _logger.info("Cloning cats for: %s" % master_category_ids)
    service = CategoryService.get_instance()
    categories = []
    for cat_id in master_category_ids:
        category = service.clone_top_level_cat(cat_id, seller_id)
        models.db.session.commit()
        if category:
            categories.append(category)
        else:
            _logger.error("Not cloning master cat: %s for seller : %s" % (cat_id, seller_id))
    kwargs['category_ids'] = [cat.id for cat in categories]
    kwargs['seller_id'] = seller_id
    create_categories_on_SRM.apply_async(kwargs=kwargs, countdown=10)


def can_create_category_on_srm(cat, seller_id=None):
    payload = {
        "taxInCode": cat.tax_in_code,
        "code": cat.code,
        "isActive": cat.is_active,
        "name": cat.name,
        "taxOutCode": cat.tax_out_code,
        "parent": int(cat.parent_id) if cat.parent_id else 0,
        "sellerId": seller_id or cat.seller_id,
        "feId": cat.id,
        "queued": False
    }
    _logger.info(payload)
    resp = requests.post(url=config.SRM_SERVICE_URL + '/categories', json=payload)
    _logger.info(resp.status_code)
    _logger.info(resp.content)
    if resp.status_code != 200:
        _logger.info("Failed, not sync all data to SRM")
        return False
    else:
        _logger.info("Success, can sync all data to SRM")
    return True


@celery.task(queue='clone_master_categories')
def create_categories_on_SRM(**kwargs):
    service = CategoryService.get_instance()
    if not kwargs.get("category_ids") or not kwargs.get("seller_id"):
        return
    category_ids = kwargs.get("category_ids")
    seller_id = kwargs.get("seller_id")

    if config.SYNC_CATEGORY_TO_SRM_REPEAT_TIME != 0 and (
            kwargs.get('retried_time', 0) > config.SYNC_CATEGORY_TO_SRM_REPEAT_TIME):
        _logger.info("Reached the limit time to retry create category to SRM: %s times" % kwargs.get('retried_time', 0))
        return

    try:
        first_cat = service.get_category_tree(category_ids[0], seller_id)
        can_sync_srm = can_create_category_on_srm(first_cat)
        if not can_sync_srm:
            raise RuntimeError("Failed to create category on SRM url: %s" % (config.SRM_SERVICE_URL + '/categories'))
    except Exception as e:
        # retry after 1 hour
        _logger.exception(e)
        kwargs['retried_time'] = kwargs.get('retried_time', 0) + 1
        create_categories_on_SRM.apply_async(kwargs=kwargs, countdown=int(config.SYNC_CATEGORY_TO_SRM_DELAY_TIME))
        return

    service = CategoryService.get_instance()
    for cat_id in kwargs.get("category_ids"):
        cat_tree = service.get_category_tree(cat_id, kwargs.get("seller_id"))
        if cat_tree:
            service.create_category_on_srm(cat_tree)


@signals.on_category_apply_shipping_type_to_sku
def send_apply_shipping_type_to_sku_message_to_celery(category_id):
    process_apply_shipping_type_to_sku_message_to_celery.delay(category_id=category_id, required_login=True)


@celery.task
def process_apply_shipping_type_to_sku_message_to_celery(category_id, **kwargs):
    # update product_details
    try:
        entity = models.Category.query.get(category_id)

        update_sql = text("""update product_details pd set pd.`data` = JSON_SET(pd.`data`, '$.shipping_types', 
                                (select JSON_ARRAYAGG(st.`code`) from sellable_products sp
                                    join sellable_product_shipping_type spst on sp.id = spst.sellable_product_id
                                    join shipping_types st on spst.shipping_type_id = st.id 
                                        where sp.sku = pd.sku)), updated_by = :updated_by
                            where pd.sku in ((select sp.sku as sellable_product_id from sellable_products sp
                                where sp.category_id in (SELECT cat.id 
                                    from categories cat where cat.id = :category_id 
                                                            or cat.path like :path)))""")

        db.engine.execute(update_sql,
                          category_id=category_id,
                          path=f'{entity.path}/%',
                          updated_by=kwargs.get('_rq_ctx_user_email', ""))
        db.session.commit()
    except Exception as e:
        _logger.exception(e)

    # send product message to connector
    # noinspection PyBroadException
    try:
        entity = models.Category.query.get(category_id)
        category_ids = [x.id for x in models.Category.query.filter(or_(
            models.Category.id == category_id,
            models.Category.path.like(f'{entity.path}/%'))).with_entities(models.Category.id).all()]
        sellable_products = models.SellableProduct.query \
            .filter(models.SellableProduct.category_id.in_(category_ids)).all()
        for sellable_product in sellable_products:
            routing_key = 'teko.catalog.sellable.updated'
            data = SellableUpdateSchema().dump(sellable_product)
            message_scheme = sellable_update_pb2.SellableUpdateMessage()
            message = json_format.ParseDict(data, message_scheme, ignore_unknown_fields=True)
            publisher = queue_publisher.QueuePublisher()
            headers = {'X-feid': str(sellable_product.id)}
            publisher.publish_message(
                message=message.SerializeToString(),
                routing_key=routing_key,
                headers=headers
            )
    except Exception as e:
        _logger.exception(e)
