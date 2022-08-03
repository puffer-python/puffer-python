from flask_login import current_user
from marshmallow import ValidationError

from catalog.extensions import marshmallow as mm
from catalog import celery, validators, app
from catalog.biz.product_import import ImportHandler
from catalog.extensions import exceptions
from catalog.extensions.exceptions import BadRequestException
from catalog.extensions import signals
from catalog.services.products.sellable import update_terminal_groups_for_sellable, get_skus_by_filter
from catalog.validators import imports as validators
import numpy as np
from catalog import models as m


@signals.on_update_product_terminal_groups_imported
def on_update_product_terminal_groups_imported(params):
    update_terminal_groups.delay(params, send_environ=True)


@celery.task(queue='import_update_product_terminal_groups')
def update_terminal_groups(params, environ=None):
    with app.request_context(environ):
        importer = ImportTerminalGroupsHandler(params['id'])
        importer.process()


class ImportTerminalGroupsHandler(ImportHandler):
    _VALIDATOR_CLASS = validators.UploadFileUpdateProductTerminalGroupsValidator

    def _process_row(
            self, index,
            seller_sku, uom_name, uom_ratio, terminal_groups, terminal_groups_delete,
            *args, **kwargs):
        try:
            seller_sku = None if seller_sku is np.NAN else str(seller_sku).strip()
            uom_name = None if uom_name is np.NAN else str(uom_name).strip()
            uom_ratio = None if uom_ratio is np.NAN else str(uom_ratio).strip()
            terminal_groups = None if terminal_groups is np.NAN else str(terminal_groups).strip()
            terminal_groups_delete = None if terminal_groups_delete is np.NAN\
                                            else str(terminal_groups_delete).strip()

            if seller_sku is None:
                raise ValueError('Chưa nhập seller sku')
            if not terminal_groups and not terminal_groups_delete:
                raise ValueError('Chưa nhập terminal groups để xóa hoặc thêm mới')

            sellable = get_skus_by_filter(
                seller_id=current_user.seller_id,
                seller_sku=seller_sku,
                uom_name=uom_name,
                uom_ratio=uom_ratio,
                only_one=True)

            if not sellable:
                raise exceptions.BadRequestException('Sản phẩm không tồn tại')

            data = {
                'sellable_product_id': sellable.id,
                'terminal_groups_new': terminal_groups,
                'terminal_groups_delete': terminal_groups_delete
            }
            update_terminal_groups_for_sellable(**data)

        except ValidationError as error:
            self._result[index] = mm.format_errors(error)
        except BadRequestException as error:
            self._result[index] = error.message
        except Exception as error:
            self._result[index] = str(error)
        else:
            self._success_rows.append(sellable.sku)
            self._result[index] = 'Thành công'
            self._process.total_row_success += 1

    def _send_success_signals(self):
        signals.listing_update_signal.send(self._success_rows)
