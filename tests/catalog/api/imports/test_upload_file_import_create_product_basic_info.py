# coding=utf-8

import io
import json
import os

import requests
from mock import patch
import pandas as pd
import numpy as np
from werkzeug.datastructures import FileStorage

from catalog.services.imports import FileImportService
from config import MAX_IMPORT_FILE_PENDING
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


TITLE_ROW_OFFSET = 6
service = FileImportService.get_instance()


class CreateProductBasicInfo(APITestCase):
    ISSUE_KEY = 'CATALOGUE-330'
    FOLDER = '/Import/Create_product_basic_info'

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

        self.patcher_post = patch('catalog.services.imports.file_import.requests.post')
        self.patcher_signal = patch('catalog.services.imports.file_import.signals.product_basic_info_import_signal.send')

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
        return '/import?type=create_product_basic_info'

    def method(self):
        return 'POST'

    def test_200_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url(), content_type='multipart/form-data', data=self.data)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'File được tải lên thành công')
            self.mock_signal.assert_called_once()

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
            self.assertEqual(body['message'], 'Hệ thống đang bị quá tải số lượng file cần xử lý. Vui lòng thực hiện sau')

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
