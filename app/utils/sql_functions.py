# coding=utf-8
import logging
import os

from sqlalchemy import text

import config
from catalog.models import db

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


def select_and_insert_json(sellable_sku, updated_by=""):
    """

    :param sellable_sku
    :param updated_by
    :return:
    """
    with open(os.path.join(config.ROOT_DIR, 'catalog', 'utils', 'select_listing.sql'), 'r') as file:
        sql = file.read()
        sql += ' WHERE a.sku = :sku'
        select_result = db.engine.execute(text(sql), sku=sellable_sku)

    insert_into_values_on_duplicate = text(""" 
insert into product_details (sku, data, updated_by, created_at, updated_at)
values (:sku, :product_json, :updated_by, now(), now())
ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = now(), updated_by = :updated_by
""")
    values = []
    for record in select_result:
        values.append({
            'sku': record.sku,
            'product_json': record.product_json,
            'updated_by': updated_by
        })

    db.engine.execute(insert_into_values_on_duplicate, *values)
    db.session.commit()



def update_by_brand(brand_id, updated_by=""):
    with open(os.path.join(config.ROOT_DIR, 'catalog', 'utils', 'select_listing.sql'), 'r') as file:
        sql = file.read()
        sql += f' WHERE a.brand_id = {brand_id}'

    update_sql = text(
        f"""update product_details, ({sql}) s set data = s.product_json, updated_at = now(), updated_by = :updated_by
            where product_details.sku = s.sku""")

    db.engine.execute(update_sql, updated_by=updated_by)


def update_by_attribute(attribute_id, option_id=None, updated_by=""):
    with open(os.path.join(config.ROOT_DIR, 'catalog', 'utils', 'select_listing.sql'), 'r') as file:
        sql = file.read()
        condition = """ WHERE exists (SELECT va.id from variant_attribute va WHERE va.variant_id = a.variant_id
                AND va.attribute_id = {attribute_id} AND va.value {option_condition})"""
        if option_id:
            condition = condition.format(attribute_id=attribute_id, option_condition=f' = {option_id}')
        else:
            condition = condition.format(attribute_id=attribute_id, option_condition=' IS NOT NULL')
        sql += condition

    update_sql = text(
        f"""update product_details, ({sql}) s set data = s.product_json, updated_at = now(), updated_by = :updated_by
                where product_details.sku = s.sku""")

    db.engine.execute(update_sql, updated_by=updated_by)
