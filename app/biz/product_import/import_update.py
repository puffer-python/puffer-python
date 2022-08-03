# coding=utf-8

import io
from abc import abstractmethod
from enum import Enum
import uuid
import pandas as pd
import config
import requests

from catalog import (
    models,
    app,
    celery,
    utils,
)
from catalog.utils import highlight_error
from catalog.biz.product_import.import_update_product_attribute import UpdateProductAttributeImporter
from catalog.biz.product_import.import_update_product_basic_info import GeneralUpdateImporter
from catalog.extensions import signals

from catalog.services.products.variant import ProductVariantService
from catalog.extensions.exceptions import BaseHTTPException

variant_service = ProductVariantService.get_instance()


class ImportException(BaseHTTPException):
    def __init__(self, sku=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sku = sku


class Status(Enum):
    SUCCESS = 'Success'
    ERROR = 'Error'

    def __str__(self):
        return self.value


def coroutine(fn):
    def decorator(*args, **kwargs):
        co = fn(*args, **kwargs)
        next(co)
        return co

    return decorator


class ImporterABC:
    SKIP_ROWS = None
    SHEET_NAME = None
    RESULT_HEADER = ('SKU', 'Status', 'Message')

    def __init__(self, task_id):
        self.task_id = task_id
        self.task = None
        self.result = pd.DataFrame(columns=self.RESULT_HEADER, dtype=object)
        self.total_row_success = 0
        self.excel_field_names = []

    def _fetch_file_import(self):
        """Query FileImport for get url excel file"""
        self.task = models.FileImport.query.get(self.task_id)
        if not self.task:
            raise RuntimeError('FileImport not found')
        self.df = pd.read_excel(
            io=self.task.path,
            sheet_name=self.SHEET_NAME,
            skiprows=self.SKIP_ROWS,
            keep_default_na=False,
            dtype=str,
        )
        self.excel_field_names = self.df.columns

    @staticmethod
    def yes_no_mapping(x=None):
        if x is not None:
            x = str(x)
            if x in ('1', 'Yes'):
                return True
            elif x in ('0', 'No'):
                return False

    @staticmethod
    def date_type_mapping(x=None):
        if x is not None:
            x = str(x)
            if x == 'Ngày':
                return 1
            elif x == 'Tháng':
                return 2

    @abstractmethod
    def _load_resource(self):
        return NotImplemented

    @abstractmethod
    def _mapping_data(self, next_):
        return NotImplemented

    @abstractmethod
    def _process_data(self, next_):
        return NotImplemented

    @coroutine
    def _export_result(self):
        task = self.task
        while True:
            sku, status, msg = yield
            self.result = self.result.append(pd.Series(
                (sku, status, msg), index=self.RESULT_HEADER
            ), ignore_index=True)

            task.total_row_success += status == Status.SUCCESS

    def _execute(self):
        self.task.status = 'processing'
        self.task.total_row_success = 0
        models.db.session.commit()

        try:
            # mapping -> main process -> export result
            process = self._mapping_data(self._process_data(self._export_result()))
            for _, row in self.df.iterrows():
                function_caller = getattr(process, 'send')
                function_caller(row)

        except Exception as error:
            self.task.status = 'error'
            self.task.note = str(error)
        else:
            # write and upload file
            file = io.BytesIO()
            self.result.style.apply(highlight_error, axis=1).to_excel(file, 'Result', index=False)
            file.seek(0)
            report_url = self.upload_result_to_server(file)

            # update FileImport
            self.task.status = 'done'
            self.task.success_path = report_url
        finally:
            models.db.session.commit()

    def run(self):
        self._fetch_file_import()
        self._load_resource()
        self._execute()

    def upload_result_to_server(self, file):
        """Upload importing result to file service"""
        upload_form = {'file': (
            f'{uuid.uuid4()}.xlsx',
            file,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )}
        resp = requests.post('{}/upload/doc'.format(config.FILE_API), files=upload_form)
        if resp.status_code != 200:
            raise RuntimeError('Result file can not upload to server')
        return resp.json().get('url')


@celery.task(
    queue='import_update_products'
)
def update_product_task(task_id, environ):
    executor = GeneralUpdateImporter(task_id)
    with app.request_context(environ):
        executor.run()


@celery.task(
    queue='import_update_products'
)
def update_product_attribute_task(task_id, environ):
    executor = UpdateProductAttributeImporter(task_id)
    with app.request_context(environ):
        executor.run()


@signals.on_update_product_import
def async_update_products(params):
    environ = utils.environ2json()
    update_product_task.delay(
        task_id=params.get('id'),
        environ=environ
    )


@signals.on_update_attribute_product_import
def async_update_attribute_products(params):
    environ = utils.environ2json()
    update_product_attribute_task.delay(
        task_id=params.get('id'),
        environ=environ
    )
