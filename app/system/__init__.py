# coding=utf8

import json
import os
import logging

from flask import request
from sqlalchemy import or_

from catalog import app, metrics, cache, celery, models
from catalog.models import db
from catalog.utils.sql_functions import select_and_insert_json

_logger = logging.getLogger(__name__)


@app.route('/health')
@metrics.do_not_track()
def __health():
    return 'ok'


@app.route('/health/live')
@metrics.do_not_track()
def __health_live():
    return 'ok'


@app.route('/health/ready')
@metrics.do_not_track()
def __health_ready():
    return 'ok'


@app.route('/doc', methods=['GET'])
def doc():
    return app.send_static_file('docs/index.html')


@app.route('/getversion')
def __get_version():
    return os.getenv('IMAGE_TAG', 'N/A')


@app.route('/system/clear-cache')
def clear_cache():
    with app.app_context():
        cache.clear()
    return 'ok'


@app.route('/system/brands/<int:brand_id>/sync')
def brand_sync(brand_id):
    from catalog.models.brand import Brand
    brand = Brand.query.get(brand_id)
    import requests
    rq = requests.put('http://supplier-api-v2-api.supplier-management/api/brands/{}/'.format(brand.code), json={
        'code': brand.internal_code,
        'name': brand.name,
        'isActive': brand.is_active

    })
    _logger.info(rq.status_code)
    _logger.info(rq.text)
    return rq.text


@app.route('/system/brands/<int:brand_id>/to_srm')
def brand_to_srm(brand_id):
    from catalog.models.brand import Brand
    brand = Brand.query.get(brand_id)
    from catalog.extensions import signals
    if brand:
        signals.brand_created_signal.send(brand)
        models.db.session.commit()
        return 'done'
    return 'invalid brand_id'


@app.route('/system/sellable_product/<int:p_id>/up_srm')
def sellable_product_up_srm(p_id):
    from catalog.models.sellable_product import SellableProduct
    sellable_product = SellableProduct.query.get(p_id)
    from catalog.extensions import signals
    signals.sellable_common_update_signal.send(sellable_product)
    return 'done'


@app.route('/system/sellable_product/retry_create', methods=['POST'])
def sellable_product_retry_create():
    from catalog.extensions import signals
    from catalog.models.sellable_product import SellableProduct
    from flask import request
    sql_str = request.get_data(cache=False, as_text=True)
    data = json.loads(sql_str)
    skus = data.get("skus", [])
    sellable_products = SellableProduct.query.filter(
        SellableProduct.sku.in_(skus)
    ).all()
    for sellable_product in sellable_products:
        signals.sellable_create_signal.send(sellable_product)
    return 'done'


@app.route('/system/sellable_products/update_to_srm', methods=['GET', 'POST'])
def update_multi_skus_to_srm():
    from catalog.models.sellable_product import SellableProduct
    from catalog.biz.sellable import on_sellable_updated
    ids = request.args.get('ids') or request.form.get('ids') or ''
    skus = request.args.get('skus') or request.form.get('skus') or ''
    if not ids and not skus:
        return 'None'
    sellable_products = SellableProduct.query.filter(
        or_(
            SellableProduct.id.in_(ids.split(',')),
            SellableProduct.sku.in_(skus.split(',')),
            SellableProduct.seller_sku.in_(skus.split(','))
        )).all()
    if sellable_products:
        for sku in sellable_products:
            on_sellable_updated(sku)
    return 'done'


@app.route('/system/sellable_products/create_to_srm', methods=['GET', 'POST'])
def create_multi_skus_to_srm():
    from catalog.models.sellable_product import SellableProduct
    from catalog.biz.sellable import on_sellable_created
    ids = request.args.get('ids') or request.form.get('ids') or ''
    skus = request.args.get('skus') or request.form.get('skus') or ''
    sellable_products = SellableProduct.query.filter(
        or_(
            SellableProduct.id.in_(ids.split(',')),
            SellableProduct.sku.in_(skus.split(',')),
            SellableProduct.seller_sku.in_(skus.split(','))
        )).all()
    if sellable_products:
        for sku in sellable_products:
            on_sellable_created(sku)
    return 'done'


@app.route('/system/category/<int:c_id>/create')
def system_category_create(c_id):
    from catalog.models.category import Category
    from catalog.extensions import signals
    category = Category.query.get(c_id)
    signals.category_created_signal.send(category)
    return 'done'


@app.route('/system/sellable_products/product_details', methods=['GET', 'POST'])
def sync_product_detail():
    skus = request.args.get('skus') or request.json.get('skus') or request.form.get('skus') or ''
    v2 = request.args.get('v2') or request.json.get('v2') or request.form.get('v2') or ''
    skus = skus.split(',')
    update_product_details.delay(skus, 'system')
    if v2:
        update_product_details_v2.delay(skus, 'system')
    return 'done'


@app.route('/system/env', methods=['POST'])
def system_env():
    from flask import request
    import json
    key = request.get_data(as_text=True)
    return json.dumps({'data': app.config.get(key)})


@app.route('/system/units/<int:u_id>/to_srm')
def unit_to_srm(u_id):
    from catalog.models.unit import Unit
    unit = Unit.query.get(u_id)
    from catalog.extensions import signals
    signals.unit_created_signal.send(unit)
    db.session.commit()
    return 'done'


@app.route('/system/units/<int:u_id>/update_to_srm')
def update_unit_to_srm(u_id):
    from catalog.models.unit import Unit
    unit = Unit.query.get(u_id)
    from catalog.extensions import signals
    signals.unit_updated_signal.send(unit)
    db.session.commit()
    return 'done'


@celery.task
def run_sql(sql_str):
    db.engine.execute(sql_str)


@celery.task()
def update_product_details(skus, updated_by):
    for sku in skus:
        select_and_insert_json(sku, updated_by)
    pass


@celery.task()
def update_product_details_v2(skus, updated_by):
    from catalog import producer
    from catalog.constants import RAM_QUEUE
    for sku in skus:
        producer.send(message={"sku": sku, "updated_by": updated_by},
                      event_key=RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL_V2,
                      connection=models.db.session)
    pass


@app.route('/install', methods=['POST'])
def install():
    from flask import request
    sql_str = request.get_data(cache=False, as_text=True)
    run_sql.delay(sql_str)
    return 'done'


@app.route('/query', methods=['POST'])
def query():
    from flask import request, jsonify
    sql_str = request.get_data(cache=False, as_text=True)
    results = db.engine.execute(sql_str)
    res = []
    for r in results:
        item = {}
        for column, value in r.items():
            item[column] = value
        res.append(item)

    return jsonify(res)


def map_uom(uom_code, p_sku):
    from catalog import models
    uom_attribute = models.Attribute.query.filter(
        models.Attribute.code == 'uom'
    ).first()
    option = models.AttributeOption.query.filter(
        models.AttributeOption.attribute_id == uom_attribute.id,
        models.AttributeOption.code == uom_code
    ).first()
    sku = models.SellableProduct.query.filter(
        models.SellableProduct.sku == p_sku
    ).first()
    if sku and option:
        sku.uom_code = option.code
        sku.uom_name = option.value
        variant_uom = models.VariantAttribute.query.filter(
            models.VariantAttribute.attribute_id == uom_attribute.id,
            models.VariantAttribute.variant_id == sku.variant_id
        ).first()
        variant_uom.value = option.id
        models.db.session.flush()
        from catalog.biz.sellable import on_sellable_updated
        on_sellable_updated(sku)
        from catalog.utils.sql_functions import select_and_insert_json
        select_and_insert_json(sellable_sku=sku.sku, updated_by='dung.bv@teko.vn')


@app.route('/system/uom_mapping', methods=['POST'])
def system_uom_mapping():
    from flask import request
    sql_str = request.get_data(cache=False, as_text=True)
    data = json.loads(sql_str)

    for item in data:
        map_uom(
            item.get('uom'),
            item.get('sku')
        )
    return "Your request is processed"


@app.route('/system/sellable_product_up_ppm', methods=['POST'])
def system_sellable_product_up_ppm():
    from catalog.extensions import signals
    from catalog.models.sellable_product import SellableProduct
    ids = request.args.get('ids') or request.form.get('ids') or ''
    sellable_products = SellableProduct.query.filter(
        or_(
            SellableProduct.id.in_(ids.split(',')),
        )).all()
    if sellable_products:
        for sku in sellable_products:
            signals.sellable_update_seo_info_signal.send(sku)
    return 'done'
