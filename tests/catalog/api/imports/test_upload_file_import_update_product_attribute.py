# coding=utf-8

import io
import json
import os

import requests
from mock import patch
import pandas as pd
import numpy as np
from werkzeug.datastructures import FileStorage

import config
from catalog.services.imports import FileImportService
from config import MAX_IMPORT_FILE_PENDING
from tests import logged_in_user
from tests.catalog.api import APITestCase
from catalog import models as m, models
from tests.faker import fake

TITLE_ROW_OFFSET = 6
service = FileImportService.get_instance()


class UploadFileImportUpdateProductAttribute(APITestCase):
    ISSUE_KEY = 'CATALOGUE-644'
    FOLDER = '/Import/UploadFileImportUpdateProductAttribute'

    def setUp(self):
        self.user = fake.iam_user()

        self.patcher_post = patch('catalog.services.imports.file_import.requests.post')
        self.patcher_signal = patch(
            'catalog.services.imports.file_import.signals.update_attribute_product_import_signal.send')

        self.mock_post = self.patcher_post.start()
        self.mock_signal = self.patcher_signal.start()

        resp = requests.Response()
        resp.status_code = 200
        resp._content = json.dumps({}).encode('utf-8')
        self.mock_post.return_value = resp

    def tearDown(self):
        self.patcher_post.stop()
        self.patcher_signal.stop()

    def url(self):
        return '/import?type=update_attribute_product'

    def method(self):
        return 'POST'

    @staticmethod
    def read_file(file_name, **kwargs):
        file_path = os.path.join(
            config.ROOT_DIR,
            'tests',
            'catalog',
            'api',
            'imports',
            'test_case_samples',
            'update_product_attribute',
            file_name
        )
        with open(file_path, 'rb') as f:
            file_content = f.read()
        data_stream = io.BytesIO(file_content)
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        if file_name.endswith('.xls'):
            content_type = 'application/vnd.ms-excel'
        data = FileStorage(
            stream=data_stream,
            filename=file_name,
            content_type=kwargs.get('content_type', content_type),
            content_length=len(file_content)
        )
        return {
            'file': data
        }

    def assert_upload_file_success(self, file_name, row_count):
        code, body = self.call_api_with_login(url=self.url(), content_type='multipart/form-data',
                                              data=self.read_file(file_name))
        self.assertEqual(200, code)
        self.assertEqual(body['message'], 'File được tải lên thành công')

        id = body['result']['id']
        import_file = m.FileImport.query.get(id)
        self.assertEqual(row_count, import_file.total_row)
        self.mock_signal.assert_called_once()

    def assert_upload_file_fail(self, file_name, message=None):
        code, body = self.call_api_with_login(url=self.url(), content_type='multipart/form-data',
                                              data=self.read_file(file_name))
        self.assertEqual(400, code)
        if message:
            self.assertEqual(body['message'], message)

    def test_return200__xlsx_Has_A_Data(self):
        self.assert_upload_file_success('has_one_data.xlsx', 1)

    def test_return200__xls_Has_A_Data(self):
        self.assert_upload_file_success('has_one_data.xls', 1)

    def test_return200__xlsx_Has_1000_Data(self):
        self.assert_upload_file_success('has_1000_data.xlsx', 1000)

    def test_return200__xls_Has_1000_Data(self):
        self.assert_upload_file_success('has_1000_data.xls', 1000)

    def test_return400__xlsx_No_Data(self):
        self.assert_upload_file_fail('no_data.xlsx', 'File không có dữ liệu')

    def test_return400__xls_No_Data(self):
        self.assert_upload_file_fail('no_data.xls', 'File không có dữ liệu')

    def test_return400__xlsx_Has_1001_Data(self):
        self.assert_upload_file_fail('has_1001_data.xlsx', 'Số lượng sản phẩm trong file không được quá 1 nghìn dòng')

    def test_return400__xls_Has_1001_Data(self):
        self.assert_upload_file_fail('has_1001_data.xls', 'Số lượng sản phẩm trong file không được quá 1 nghìn dòng')

    def test_return400__Invalid_File(self):
        self.assert_upload_file_fail('invalid.txt',
                                     'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')

    def test_return400__Invalid_Sheet_Name(self):
        self.assert_upload_file_fail('invalid_sheet_name.xlsx',
                                     'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')

    def test_return400__Invalid_Version(self):
        fake.misc(data_type='import_type', code='update_product', config='{"version":3}')
        self.assert_upload_file_fail('invalid_version.xlsx',
                                     'Mẫu file import của bạn đã cũ. Vui lòng tải lại file mẫu mới để thực hiện')
