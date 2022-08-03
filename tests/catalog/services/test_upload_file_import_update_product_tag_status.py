# coding=utf-8

import io
from mock import patch
import json
from mock import patch

import pytest
import requests
import pandas as pd
import numpy as np
from werkzeug.datastructures import FileStorage

from catalog.extensions import exceptions as exc
from catalog.services.imports import FileImportService
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake

TITLE_ROW_OFFSET = 2
service = FileImportService.get_instance()

class UploadFileImportProductTestCase(APITestCase):
    ISSUE_KEY = 'SC-612'

    def setUp(self):
        out = io.BytesIO()
        self.total_row = fake.random_int(50)
        df = pd.DataFrame(data=np.random.random((TITLE_ROW_OFFSET + self.total_row, 20))).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )

        self.user = fake.iam_user()
        self.url = fake.url()

    def assertResponse(self, import_record):
        assert import_record.path == self.url
        assert import_record.created_by == self.user.email
        assert import_record.seller_id == self.user.seller_id
        assert import_record.status == 'new'
        assert import_record.type == 'tag_product'
        assert import_record.name == self.file.filename
        assert import_record.total_row == self.total_row
        assert len(import_record.key) == 10

    @patch('requests.post')
    @patch('catalog.extensions.signals.update_product_tag_import_signal.send')
    def test_passValiddata__returnImportRecord(self, mock_signal, mock_request):
        resp = requests.Response()
        resp.status_code = 200
        resp._content = json.dumps({
            'url': self.url
        }).encode('utf-8')
        mock_request.return_value = resp
        mock_signal.return_value = None
        import_record = service.import_update_product_tag(self.file, self.user)
        self.assertResponse(import_record)

    @patch('requests.post')
    @patch('catalog.extensions.signals.update_product_tag_import_signal.send')
    def test_raiseException__whenCallFileServiceFail(self, mock_signal, mock_request):
        resp = requests.Response()
        resp.status_code = 400
        resp._content = json.dumps({}).encode('utf-8')
        mock_request.return_value = resp
        mock_signal.return_value = None
        with pytest.raises(exc.BadRequestException) as error_info:
            service.import_update_product_tag(self.file, self.user)
        assert error_info.value.message == 'Upload file không thành công'
