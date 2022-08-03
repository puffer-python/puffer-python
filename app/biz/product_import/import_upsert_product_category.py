import uuid

import pandas as pd
import numpy as np
import io

import requests
import config

from catalog import celery, app
from catalog.utils import highlight_error
from catalog.extensions import signals
from catalog import models as m
from catalog.extensions.exceptions import BadRequestException
from marshmallow import ValidationError
from catalog.extensions import marshmallow as mm
from catalog.utils import safe_cast

_TITLE_ROW_OFFSET = 3
_SHEET_NAME = 'DuLieuNhap'


@signals.on_upsert_product_category_imported
def on_upsert_product_category_imported(params):
    upsert_product_categories.delay(
        params, send_environ=True
    )


def _get_map_skus(sellable_products):
    map_sku = {}
    for sku in sellable_products:
        skus = map_sku.get(sku.seller_sku)
        if not skus:
            skus = []
        skus.append(sku)
        map_sku[sku.seller_sku] = skus
    return map_sku


def _get_map_categories(category_ids):
    if not category_ids:
        return {}
    categories = m.Category.query.filter(m.Category.id.in_(category_ids))
    categories = {i.id: i for i in categories}
    return categories


def _get_map_product_categories(product_ids):
    if not product_ids:
        return {}
    product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id.in_(product_ids)).all()
    category_ids = list(map(lambda x: x.category_id, product_categories))
    map_categories = _get_map_categories(category_ids)
    map_product_categories = {}
    for product_cat in product_categories:
        categories = map_product_categories.get(product_cat.product_id)
        if not categories:
            categories = []
        item = (product_cat, map_categories.get(product_cat.category_id))
        categories.append(item)
        map_product_categories[product_cat.product_id] = categories
    return map_product_categories


def _upsert_product_category(product_category, product_id, category_id, created_by):
    if product_category:
        product_category.category_id = category_id
        product_category.created_by = created_by
    else:
        product_category = m.ProductCategory()
        product_category.product_id = product_id
        product_category.category_id = category_id
        product_category.created_by = created_by
        m.db.session.add(product_category)


def _get_product_category(seller_id, product_id, product_categories):
    platform_categories = product_categories.get(product_id)
    product_category = None
    if platform_categories:
        for product_category, platform_category in platform_categories:
            if platform_category.seller_id == seller_id:
                break
    return product_category


def get_data_from_file(df):
    map_sku_categories = {}
    skus = []
    category_ids = []
    for index, (seller_sku, category_id) in df.iterrows():
        seller_sku = None if seller_sku is np.NAN else str(seller_sku).strip()
        category = None if category_id is np.NAN else str(category_id).strip()
        category_id = None
        if category:
            category_id = category.split('=>')[0]
            category_id = safe_cast(category_id, int)
        if seller_sku:
            skus.append(seller_sku)
        if category_id:
            category_ids.append(category_id)
        map_sku_categories[index] = (seller_sku, category_id)
    return map_sku_categories, skus, category_ids


@celery.task()
def upsert_product_categories(params, on_success=None, on_error=None, environ=None):
    with app.request_context(environ):
        try:
            # ---------------- change status to processing
            sellable_success = list()
            import_process = m.FileImport.query.get(params['id'])
            if not import_process:
                return
            platform_id = params.get('platform_id') or import_process.platform_id
            if not platform_id:
                import_process.status = 'done'
                return

            platform_owner = m.PlatformSellers.query.filter(m.PlatformSellers.platform_id == platform_id,
                                                            m.PlatformSellers.is_owner.is_(True)).first()
            if not platform_owner:
                import_process.status = 'done'
                return
            created_by = params.get('created_by') or import_process.created_by or 'system'
            import_process.status = 'processing'
            m.db.session.commit()

            # --------------- start importing
            df = pd.read_excel(import_process.path, header=_TITLE_ROW_OFFSET,
                               sheet_name=_SHEET_NAME, keep_default_na=False, ).convert_dtypes()
            result = [""] * df.shape[0]
            import_process.total_row_success = 0
            map_sku_categories, skus, category_ids = get_data_from_file(df)

            sellable_products = m.SellableProduct.query.filter(
                m.SellableProduct.seller_sku.in_(skus),
                m.SellableProduct.seller_id == import_process.seller_id
            ).all()
            product_ids = list(map(lambda x: x.product_id, sellable_products))
            product_categories = _get_map_product_categories(product_ids)
            sellable_products = _get_map_skus(sellable_products)
            categories = _get_map_categories(category_ids)
            map_processed_product_categories = {}
            for (index, data) in map_sku_categories.items():
                try:
                    seller_sku, category_id = data

                    if seller_sku is None:
                        raise ValueError('Chưa nhập seller sku')
                    if category_id is None:
                        raise ValueError('Chưa nhập danh mục ngành hàng')
                    skus = sellable_products.get(seller_sku)

                    if not skus:
                        raise BadRequestException('Sản phẩm không tồn tại')
                    category_id = int(category_id)
                    category = categories.get(category_id)
                    if not category:
                        raise BadRequestException('Danh mục ngành hàng không tồn tại')
                    if not category.is_active:
                        raise BadRequestException('Danh mục ngành hàng bị vô hiệu')
                    if not category.is_leaf:
                        raise BadRequestException('Danh mục ngành hàng phải là lá')
                    if category.seller_id != platform_owner.seller_id:
                        raise BadRequestException('Danh mục không thuộc sàn')

                    for sku in skus:
                        sellable_success.append(sku)
                        product_id = sku.product_id
                        if map_processed_product_categories.get(product_id):
                            continue
                        product_category = _get_product_category(category.seller_id, product_id, product_categories)
                        _upsert_product_category(product_category, product_id, category_id, created_by)
                        map_processed_product_categories[sku.product_id] = sku

                except ValidationError as error:
                    result[index] = mm.format_errors(error)
                except BadRequestException as error:
                    result[index] = error.message
                except Exception as error:
                    result[index] = str(error)
                else:
                    result[index] = 'Thành công'
                    import_process.total_row_success += 1

            df.insert(len(df.columns), 'Kết quả', result, True)
            out = io.BytesIO()
            df.style.apply(highlight_error, axis=1).to_excel(out, index=None)
            out.seek(0)

            upload_url = config.FILE_API + '/upload/doc'
            resp = requests.post(
                url=upload_url,
                files={'file': (
                    f'{uuid.uuid4()}.xlsx',
                    out,
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }
            )
            if resp.status_code != 200:
                raise RuntimeError(f'Upload kết quả không thành công.\n{resp.json()}')

            import_process.success_path = resp.json()['url']
            import_process.status = 'done'
            if callable(on_success):
                on_success(df)
            return result
        except Exception as error:
            import_process.status = 'error'
            if callable(on_error):
                on_error(error)
        finally:
            m.db.session.commit()
            if sellable_success:
                for success_sku in sellable_success:
                    signals.sellable_common_update_signal.send(success_sku)
                for (_, success_sku) in map_processed_product_categories.items():
                    signals.sellable_update_signal.send(success_sku)
