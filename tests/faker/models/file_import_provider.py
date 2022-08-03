# coding=utf-8
import json
import logging
import pandas
import random
import datetime as dt
import faker.providers
import secrets

from catalog import models as m
from tests.faker import fake

__author__ = 'thiem.nv'
_logger = logging.getLogger(__name__)


class FileImportProvider(faker.providers.BaseProvider):
    """
    """
    import_types = ['create_product', 'create_product_basic_info', 'update_product', 'update_editing_status']
    import_statuses = ['new', 'processing', 'done', 'error']

    def file_import(self, type=None, status=None, created_at=None,
                    user_info=None, path=None, total_row=None, **kwargs):
        file_import = m.FileImport()
        file_import.type = type or random.choice(self.import_types)
        file_import.name = fake.unique_str(6)
        file_import.path = fake.url() if path is None else path
        file_import.success_path = fake.url()
        file_import.status = random.choice(self.import_statuses) if status is None else status
        file_import.total_row = total_row
        if file_import.status == 'success':
            file_import.total_row = fake.integer(1000) + 1
            file_import.total_row_success = fake.integer(file_import.total_row)
        file_import.created_at = dt.datetime.now() if not created_at else created_at
        if not user_info:
            user_info = fake.iam_user()
        file_import.created_by = user_info.email
        file_import.seller_id = user_info.seller_id
        file_import.attribute_set_id = kwargs.get('set_id') if 'set_id' in kwargs \
            else fake.attribute_set().id
        file_import.key = fake.text(30)
        m.db.session.add(file_import)
        m.db.session.flush()

        return file_import

    def get_import_types(self):
        return self.import_types

    def get_import_statuses(self):
        return self.import_statuses


class FakeImporterWithRow():
    row = None

class ResultImportProvider(faker.providers.BaseProvider):
    result_import_status = ['success', 'failure', 'fatal']

    def result_import(self, file_import, data=None, status=None, message=None):
        result_import = m.ResultImport()
        result_import.import_id = file_import.id
        result_import.updated_by = file_import.created_by
        result_import.message = message or None
        result_import.data = data or {'Name': fake.name()}
        result_import.status = status or fake.random_element(self.result_import_status)
        m.db.session.add(result_import)
        m.db.session.flush()
        return result_import

    def result_import_row(self, **kwargs):
        data = {
            "uom": "Bag",
            "type": "DON",
            "brand": "1980 Books",
            "model": "",
            "barcode": "b18032010312",
            "category": "01-N001-01-01-01=>Laptop Acer Option 1.1",
            "part number": "p180320213",
            "uom_ratio": "1",
            "image urls": "https://lh3.googleusercontent.com/FjoZiElbmwWT9QfwHU_7WNcQxA0ulbkTRzbf2lwBxPIlblypUEysKluP9g4MzeilyEWSvEJxc2gXEB8mCQCffljErAn8gKR5sQ",
            "vendor tax": "Thuế 10%",
            "description": "abc ",
            "listed price": "19000",
            "product name": "Phương test 131 cycle 1 lần 4",
            "product type": "Có thể tiêu thụ",
            "attribute set": "2825 => phương test 131",
            "warranty note": "phương note ",
            "terminal_group": "vnshop_selling_consumer,MML_SELL_0001",
            "expiration type": "Ngày",
            "expiry tracking": "Yes",
            "master category": "rau_cu=>Rau, củ, trái cây",
            "warranty months": "12",
            "short description": "test ",
            "is tracking serial?": "Yes",
            "days before Exp lock": "3",
            "allow selling without stock?": "Yes",
            "sku": "2103217070371"
        }

        for key in kwargs:
            if data.get(key):
                data[key] = kwargs[key]

        row = pandas.DataFrame.from_records([data]).loc[0]

        fake_importer = FakeImporterWithRow()
        fake_importer.row = row

        return fake_importer
