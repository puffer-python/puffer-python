# coding=utf-8
import time
from catalog import models
from .query import CategoryRepository
from catalog.extensions.signals import (
    category_created_signal,
    category_updated_signal,
)

import logging

_logger = logging.getLogger(__name__)

__DEDAULT_TAX_CODE = '10'
__UPSERT_INSERT = 'insert'
__UPSERT_UPDATE = 'update'


def __int_category_data(base_data, seller_id, parent=None):
    data = {
        'code': base_data.get('code'),
        'name': base_data.get('name'),
        'eng_name': base_data.get('eng_name'),
        'depth': 1,
        'seller_id': seller_id,
        'tax_in_code': __DEDAULT_TAX_CODE,
        'tax_out_code': __DEDAULT_TAX_CODE,
        'is_active': True,
        'manage_serial': False,
        'auto_generate_serial': False,
    }
    if parent:
        data['parent_id'] = parent.id
        data['depth'] = parent.depth + 1
    return data


def __insert_category(base_data, seller_id, parent=None):
    data = __int_category_data(base_data, seller_id, parent)
    category = CategoryRepository.transaction_insert(data)
    category.path = f'{category.id}'
    if parent:
        category.path = f'{parent.path}/{category.id}'
    return category


def __get_and_init_dic(seller_id, dic, cat, parent=None):
    code = cat.get('code')
    item = dic.get(code, {}).get('data')
    if not item:
        item = models.Category.query.filter(models.Category.code == code,
                                            models.Category.seller_id == seller_id).first()
        upsert_type = __UPSERT_UPDATE
        if item:
            item.name = cat.get('name')
            item.eng_name = cat.get('eng_name')
            if parent:
                item.parent_id = parent.id
                item.depth = parent.depth + 1
                item.path = f'{parent.path}/{item.id}'
        else:
            upsert_type = __UPSERT_INSERT
            item = __insert_category(cat, seller_id, parent)
        dic[code] = {'data': item, 'type': upsert_type}
    return item


def __init_base_data(cat, n):
    return {
        'code': cat.get(f'code{n}'),
        'name': cat.get(f'name{n}'),
        'eng_name': cat.get(f'eng_name{n}'),
    }


def __notify_connector(dic):
    for _, item in dic.items():
        category = item.get('data')
        if item.get('type') == __UPSERT_INSERT:
            category_created_signal.send(category)
        elif item.get('type') == __UPSERT_UPDATE:
            category_updated_signal.send(category)
        time.sleep(1)


def create_bulk_categories(data, seller_id):
    dic_cat1 = {}
    dic_cat2 = {}
    dic_cat3 = {}
    categories = data.get('categories', [])
    for c in categories:
        cat1 = __get_and_init_dic(seller_id, dic_cat1, __init_base_data(c, 1))
        if c.get('code2'):
            cat2 = __get_and_init_dic(seller_id, dic_cat2, __init_base_data(c, 2), cat1)
            if c.get('code3'):
                __get_and_init_dic(seller_id, dic_cat3, __init_base_data(c, 3), cat2)

    models.db.session.commit()
    # Sleep to wait for parent
    __notify_connector(dic_cat1)
    time.sleep(30)
    __notify_connector(dic_cat2)
    time.sleep(30)
    __notify_connector(dic_cat3)
