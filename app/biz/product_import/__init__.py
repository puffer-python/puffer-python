# coding=utf-8
import logging

from catalog.services.products.sellable import (
    update_sellable_editing_status,
    update_sellable_product_tag,
)
from catalog.validators.sellable import UpdateEditingStatusValidator
from catalog.api.product.sellable.schema import UpdateEditingStatusRequestBody
from catalog.biz.product_import import import_update
from catalog.biz.product_import.create_product import import_product_task
from catalog.biz.product_import.create_product_basic_info import import_product_basic_info_task
from catalog.biz.product_import.import_upsert_product_category import on_upsert_product_category_imported
from catalog.biz.product_import.images import import_variant_images
from catalog.biz.product_import.import_update_images_skus import *
from catalog.biz.product_import.import_update_seo_info import *

__author__ = 'Kien.HT'

from ...utils import highlight_error

_logger = logging.getLogger(__name__)


@signals.on_product_import
def on_product_import(params):
    """
    Product should be sent to product listing right after being created

    :param params:
    :return:
    """
    import_product_task.delay(params, send_environ=True)


@signals.on_product_basic_info_import
def on_product_basic_info_import(params):
    import_product_basic_info_task.delay(params, send_environ=True)


class ImportHandler:
    _VALIDATOR_CLASS = None  # Required to be define

    _success_rows = []
    _import_id = None
    _process = None
    _df = None
    _result = None
    _error = None
    _error_callback = None
    _success_callback = None

    def __init__(self, import_id, error_callback=None, success_callback=None):
        self._import_id = import_id
        self._error_callback = error_callback
        self._success_callback = success_callback
        if not self._VALIDATOR_CLASS:
            raise NotImplementedError("Validator class need to be defined")

    def _pre_process(self):
        self._process = m.FileImport.query.get(self._import_id)
        if not self._process:
            raise RuntimeError("Cannot find the import to be processed")
        self._process.status = 'processing'
        m.db.session.commit()

        self._df = pd.read_excel(
            self._process.path,
            sheet_name=self._VALIDATOR_CLASS.SHEET_NAME, header=self._VALIDATOR_CLASS.TITLE_ROW_OFFSET, dtype=str)
        self._result = [""] * self._df.shape[0]

    def _upload_result(self):
        self._df.insert(len(self._df.columns), 'Kết quả', self._result, True)
        out = io.BytesIO()
        self._df.style.apply(highlight_error, axis=1).to_excel(out, index=None)
        out.seek(0)

        upload_url = config.FILE_API + '/upload/doc'
        resp = requests.post(
            url=upload_url,
            files={'file': (
                f'{uuid.uuid4()}.xlsx',
                out,
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(f'Upload kết quả không thành công.\n{resp.json()}')

        return resp

    def _send_success_signals(self):
        pass

    def _process_row(self, index, *args, **kwargs):
        pass

    def process(self):
        try:
            self._pre_process()
            self._process.total_row_success = 0
            for index, (args) in self._df.iterrows():
                self._process_row(index, *args)

            upload_result = self._upload_result()

        except Exception as error:
            m.db.session.rollback()
            self._process.status = 'error'
            if callable(self._error_callback):
                self._error_callback(self._error)
        else:
            self._process.success_path = upload_result.json()['url']
            self._process.status = 'done'
            if callable(self._success_callback):
                self._success_callback(self._df)
        finally:
            m.db.session.commit()
            self._send_success_signals()


@signals.on_product_editing_status_updated_import
def on_editing_status_updated(params):
    update_editing_status_for_sellables.delay(
        params, send_environ=True
    )


@signals.on_update_product_tag_imported
def on_update_product_tag_imported(params):
    update_tag_for_sellable_products.delay(
        params, send_environ=True
    )


@celery.task(
    queue='import_product_status'
)
def update_editing_status_for_sellables(params, on_success=None, on_error=None, environ=None):
    with app.request_context(environ):
        sellable_success = list()
        TITLE_ROW_OFFSET = 1
        import_process = m.FileImport.query.get(params['id'])
        if not import_process:
            return
        import_process.status = 'processing'
        result = []
        m.db.session.commit()
        try:
            df = pd.read_excel(
                import_process.path,
                header=TITLE_ROW_OFFSET,
                dtype=str,
            )
            result = [""] * df.shape[0]

            # map name --> code
            editing_status_mapper = dict()
            for el in m.EditingStatus.query:
                editing_status_mapper[el.name] = el.code

            import_process.total_row_success = 0
            for index, (seller_sku, uom, uom_ratio, status_name, comment) in df.iterrows():
                try:
                    seller_sku = None if seller_sku is np.NAN else str(seller_sku)
                    status_name = None if status_name is np.NAN else status_name
                    comment = None if comment == np.NAN else str(comment)
                    uom_ratio = None if uom_ratio is np.NAN else float(uom_ratio)

                    if seller_sku is None:
                        raise ValueError('Chưa nhập seller sku')
                    if status_name is None:
                        raise ValueError('Chưa nhập trạng thái')
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
                    if status_name not in editing_status_mapper:
                        raise ValueError(f'Không tồn tại trạng thái {status_name}')
                    data = {
                        'ids': [sellable.id],
                        'status': editing_status_mapper[status_name],
                        'comment': comment
                    }
                    UpdateEditingStatusRequestBody().load(data)
                    UpdateEditingStatusValidator.validate({
                        'seller_id': import_process.seller_id,
                        **data
                    })
                    data['updated_by'] = import_process.created_by
                    update_sellable_editing_status(**data, auto_commit=False)
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

        except Exception as error:
            m.db.session.rollback()
            sellable_success.clear()
            import_process.status = 'error'
            if callable(on_error):
                on_error(error)
        else:
            import_process.success_path = resp.json()['url']
            import_process.status = 'done'
            if callable(on_success):
                on_success(df)
        finally:
            m.db.session.commit()
            for item in sellable_success:
                signals.sellable_update_signal.send(item)
                signals.sellable_common_update_signal.send(item)
            return result


@celery.task(
    queue='import_product_tag'
)
def update_tag_for_sellable_products(params, on_success=None, on_error=None, environ=None):
    with app.request_context(environ):
        sellable_success = list()
        TITLE_ROW_OFFSET = 2
        import_process = m.FileImport.query.get(params['id'])
        if not import_process:
            return
        import_process.status = 'processing'

        success_skus = []
        m.db.session.commit()
        result = []

        try:
            df = pd.read_excel(
                import_process.path,
                header=TITLE_ROW_OFFSET,
                dtype=str,
            )
            result = [""] * df.shape[0]
            import_process.total_row_success = 0
            for index, (sku, uom, uom_ratio, tags, overwrite) in df.iterrows():
                try:
                    sku = None if sku is np.NAN else str(sku).strip()
                    tags = None if tags is np.NAN else str(tags).strip()
                    overwrite = 'N' if overwrite is np.NAN else str(overwrite).strip()
                    uom_ratio = None if uom_ratio is np.NAN else float(uom_ratio)

                    if sku is None:
                        raise ValueError('Chưa nhập sku')
                    if tags is None:
                        raise ValueError('Chưa nhập tags')
                    sellables = m.SellableProduct.query.filter(
                        m.SellableProduct.seller_sku == sku,
                        m.SellableProduct.seller_id == import_process.seller_id,
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

                    data = {
                        'sellable_product_id': sellable.id,
                        'sku': sku,
                        'tags': tags,
                        'overwrite': overwrite
                    }

                    update_sellable_product_tag(**data, auto_commit=False)

                except ValidationError as error:
                    result[index] = mm.format_errors(error)
                except BadRequestException as error:
                    result[index] = error.message
                except Exception as error:
                    result[index] = str(error)
                else:
                    sellable_success.append(sellable)
                    success_skus.append(sellable.sku)
                    result[index] = 'Thành công'
                    import_process.total_row_success += 1

            df.insert(len(df.columns), 'Kết quả', result)
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
        except Exception as error:
            m.db.session.rollback()
            sellable_success.clear()
            import_process.status = 'error'
            if callable(on_error):
                on_error(error)
        else:
            import_process.success_path = resp.json()['url']
            import_process.status = 'done'
            if callable(on_success):
                on_success(df)
        finally:
            m.db.session.commit()
            for success_sku in sellable_success:
                signals.sellable_update_signal.send(success_sku)
            return result


from . import update_terminal_groups
from . import create_product_quickly
