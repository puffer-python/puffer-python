import uuid

import pandas as pd
import numpy as np
import io

import requests
import config

from catalog import celery, app
from catalog.extensions import signals
from catalog import models as m
from catalog.extensions.exceptions import BadRequestException
from marshmallow import ValidationError
from catalog.extensions import marshmallow as mm
from catalog.services.products.sellable import upsert_info_of_sellable_product_on_terminals
from catalog.validators.sellable import SEOInfoValidatorById
from catalog.validators.sellable import SEOInfoValidatorBySku, SEOInfoValidatorById


@signals.on_update_seo_info_import
def on_update_seo_info_import(params):
    update_seo_info_for_sellables.delay(
        params, send_environ=True
    )


@celery.task(queue='import_update_seo_info')
def update_seo_info_for_sellables(params, on_success=None, on_error=None, environ=None):
    with app.request_context(environ):
        # ---------------- change status to processing
        import_process = m.FileImport.query.get(params['id'])
        if not import_process:
            return
        import_process.status = 'processing'
        result = []
        m.db.session.commit()

        # --------------- start importing
        sellable_success = list()
        TITLE_ROW_OFFSET = 3
        try:
            df = pd.read_excel(import_process.path, header=TITLE_ROW_OFFSET, keep_default_na=False,).convert_dtypes()
            result = [""] * df.shape[0]

            import_process.total_row_success = 0
            for index, (seller_sku, uom, uom_ratio,
                        display_name, meta_title, meta_keyword, meta_description, url_key) in df.iterrows():
                try:
                    seller_sku = None if seller_sku is np.NAN else str(seller_sku).strip()
                    display_name = None if display_name is np.NAN else str(display_name).strip()
                    meta_title = None if meta_title is np.NAN else str(meta_title).strip()
                    meta_keyword = None if meta_keyword is np.NAN else str(meta_keyword).strip()
                    meta_description = None if meta_description is np.NAN else str(meta_description).strip()
                    url_key = None if url_key is np.NAN else str(url_key).strip()

                    # ------------------------- validate seller_sku, uom, uom_ratio
                    if seller_sku is None:
                        raise ValueError('Chưa nhập seller sku')

                    sellables = m.SellableProduct.query.filter(
                        m.SellableProduct.seller_sku == seller_sku,
                        m.SellableProduct.seller_id == import_process.seller_id
                    ).all()

                    if not sellables:
                        raise BadRequestException('Sản phẩm không tồn tại')
                    if len(sellables) > 1:
                        filtered_sellable = list(filter(
                            lambda sku: (sku.uom_name == uom or sku.uom_code == uom) and sku.uom_ratio == uom_ratio,
                            sellables
                        ))
                        if not filtered_sellable:
                            raise BadRequestException(
                                'Không tìm được sản phẩm với sku tương ứng, vui lòng nhập chính xác uom và uom_ratio để tìm đúng sản phẩm')
                        if len(filtered_sellable) > 1:
                            raise BadRequestException('Sản phẩm không hợp lệ')
                        sellable = filtered_sellable[0]
                    else:
                        sellable = sellables[0]

                    # --------------------- main processing
                    data = {
                        'terminal_codes': [],
                        'seo_info': {
                            'display_name': display_name,
                            "meta_title": meta_title,
                            "meta_keyword": meta_keyword,
                            "meta_description": meta_description,
                            "url_key": url_key
                        }
                    }

                    SEOInfoValidatorById.validate({
                        'seller_id': import_process.seller_id,
                        'sellable_id': sellable.id
                    })
                    upsert_info_of_sellable_product_on_terminals(
                        sellable_id=sellable.id,
                        **data,
                    )

                except ValidationError as error:
                    result[index] = mm.format_errors(error)
                except BadRequestException as error:
                    result[index] = error.message
                except Exception as error:
                    result[index] = str(error)
                else:
                    sellable_success.append(sellable)
                    result[index] = 'Thành công'
                    import_process.total_row_success += 1

            df.insert(len(df.columns), 'Kết quả', result, True)
            out = io.BytesIO()
            df.to_excel(out, index=None)
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

        except Exception as error:
            import_process.status = 'error'
            m.db.session.commit()
            if callable(on_error):
                on_error(error)
        else:
            import_process.success_path = resp.json()['url']
            import_process.status = 'done'
            if callable(on_success):
                on_success(df)
            m.db.session.commit()
        finally:
            return result

