# coding=utf-8
import io
import json
import os
from unittest.mock import patch

import numpy as np
import pandas as pd
import requests
from werkzeug.datastructures import FileStorage

import config
from catalog import models
from catalog.services.imports import FileImportService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

from config import MAX_IMPORT_FILE_PENDING


TITLE_ROW_OFFSET = 6
service = FileImportService.get_instance()
class UploadFileImportCreateProductDetailInfo(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1297'
    FOLDER = '/Import/CreateProductDetailInfo'

    def mock_file(self, **kwargs):
        out = io.BytesIO()
        pd.DataFrame(
            data=np.random.random((kwargs.get('size', 0) + TITLE_ROW_OFFSET + 1, 20))
        ).to_excel(out, 'Import_SanPham')
        out.seek(0)
        return FileStorage(
            stream=out,
            filename=fake.text(),
            content_type=kwargs.get('content_type', 'application/vnd.ms-excel')
        )

    def setUp(self):
        self.user = fake.iam_user()
        self.data = {
            'file': self.mock_file()
        }

        self.attribute_set = fake.attribute_set()

        self.patcher_post = patch('catalog.services.imports.file_import.requests.post')
        self.patcher_signal = patch('catalog.services.imports.file_import.signals.product_import_signal.send')

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
        return f'/import?type=create_product&attributeSetId={self.attribute_set.id}&timestamp={fake.integer()}'

    def method(self):
        return 'POST'

    def test_200_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'File được tải lên thành công')
            self.mock_signal.assert_called_once()

    def test_importFailed_InvalidCategory(self):
        pass

    def test_400_tooManyUploadingFiles(self):
        with logged_in_user(self.user):
            for _ in range(MAX_IMPORT_FILE_PENDING):
                self.data = {
                    'file': self.mock_file()
                }
                self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)

            self.data = {
                'file': self.mock_file()
            }
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(body['message'],
                             'Hệ thống đang bị quá tải số lượng file cần xử lý. Vui lòng thực hiện sau')

    def test_400_fileInvalidFormat(self):
        self.data = {
            'file': self.mock_file(content_type='text/plain')
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')
            self.mock_signal.assert_not_called()

    def test_400_tooManyRow(self):
        self.data = {
            'file': self.mock_file(size=1001)
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Số lượng sản phẩm trong file không được quá 1 nghìn dòng')
            self.mock_signal.assert_not_called()

    def test_400__notHavingProductData(self):
        self.data = {
            'file': self.mock_file(size=-1)
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'File không có dữ liệu')
            self.mock_signal.assert_not_called()

    def test_400_uploadAFileTooManyTimes(self):
        self.data = {
            'file': [self.mock_file(), self.mock_file()]
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Chỉ được upload 1 file 1 lần')

class UploadFileImportUpdateProductBasicInfo(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1297'
    FOLDER = '/Import/UploadFileImportUpdateProductBasicInfo'

    def mock_file(self, **kwargs):
        out = io.BytesIO()
        pd.DataFrame(
            data=np.random.random((kwargs.get('size', 0) + TITLE_ROW_OFFSET + 1, 20))
        ).to_excel(out, 'Update_SanPham')
        out.seek(0)
        return FileStorage(
            stream=out,
            filename=fake.text(),
            content_type=kwargs.get('content_type', 'application/vnd.ms-excel')
        )

    def setUp(self):
        self.user = fake.iam_user()
        self.data = {
            'file': self.mock_file()
        }

        self.patcher_post = patch('catalog.services.imports.file_import.requests.post')
        self.patcher_signal = patch(
            'catalog.services.imports.file_import.signals.update_product_import_signal.send')

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
        return f'/import?type=update_product&timestamp={fake.integer()}'

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
            'update_product_basic_info',
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
        import_file = models.FileImport.query.get(id)
        self.assertEqual(row_count, import_file.total_row)
        self.mock_signal.assert_called_once()

    def assert_upload_file_fail(self, file_name, message=None):
        code, body = self.call_api_with_login(url=self.url(), content_type='multipart/form-data',
                                              data=self.read_file(file_name))
        self.assertEqual(400, code)
        if message:
            self.assertEqual(body['message'], message)

    def test_200_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'File được tải lên thành công')
            self.mock_signal.assert_called_once()

    def test_importFailed_InvalidCategory(self):
        pass

    def test_400_tooManyUploadingFiles(self):
        with logged_in_user(self.user):
            for _ in range(MAX_IMPORT_FILE_PENDING):
                self.data = {
                    'file': self.mock_file()
                }
                self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)

            self.data = {
                'file': self.mock_file()
            }
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(body['message'],
                             'Hệ thống đang bị quá tải số lượng file cần xử lý. Vui lòng thực hiện sau')

    def test_400_fileInvalidFormat(self):
        self.data = {
            'file': self.mock_file(content_type='text/plain')
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')
            self.mock_signal.assert_not_called()

    def test_400_tooManyRow(self):
        self.data = {
            'file': self.mock_file(size=1001)
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Số lượng sản phẩm trong file không được quá 1 nghìn dòng')
            self.mock_signal.assert_not_called()

    def test_400__notHavingProductData(self):
        self.data = {
            'file': self.mock_file(size=-1)
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'File không có dữ liệu')
            self.mock_signal.assert_not_called()

    def test_400_uploadAFileTooManyTimes(self):
        self.data = {
            'file': [self.mock_file(), self.mock_file()]
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Chỉ được upload 1 file 1 lần')