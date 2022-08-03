# coding=utf-8

import os
import io

import pytest
import pandas as pd
import numpy as np
from werkzeug.datastructures import (
    FileStorage,
    ImmutableMultiDict,
)

from config import MAX_IMPORT_FILE_PENDING
from catalog.validators.imports import UploadFileUpdateProductTagValidator
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake

TITLE_ROW_OFFSET = 2


class UploadFileUpdateProductTagStatusTestCase(APITestCase):
    ISSUE_KEY = 'SC-612'

    def setUp(self):
        out = io.BytesIO()
        pd.DataFrame(data=np.random.random((TITLE_ROW_OFFSET + 1, 20))).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )

    def run_validator(self):
        files = ImmutableMultiDict({'file': self.file})
        UploadFileUpdateProductTagValidator.validate({
            'files': files,
        })

    def test_passDataValid__pass(self):
        self.run_validator()

    def test_passFileInvalidFormat__raiseBadRequestException(self):
        out = io.BytesIO(os.urandom(10))
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)'

    def test_passFileInvalidHeader__raiseBadRequestException(self):
        out = io.BytesIO()
        pd.DataFrame(data=np.random.random((1, 20))).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='text/plain'
        )
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)'

    def test_raiseBadRequestException__whenTooManyNewFile(self):
        for _ in range(MAX_IMPORT_FILE_PENDING + 1):
            fake.file_import(type='tag_product', status='new')
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Hệ thống đang bị quá tải số lượng file cần xử lý. Vui lòng thực hiện sau'

    def test_raiseBadRequestException__whenTooManyRow(self):
        out = io.BytesIO()
        pd.DataFrame(data=np.random.random((1001 + TITLE_ROW_OFFSET, 20))).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Số lượng sản phẩm trong file không được quá 1 nghìn dòng'

    def test_raiseBadRequestException__whenEmptyData(self):
        out = io.BytesIO()
        df = pd.DataFrame(data=np.random.random((TITLE_ROW_OFFSET, 20))).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'File không có dữ liệu'

    def test_uploadManyFile__raiseBadRequestException(self):
        self.file = list()
        for _ in range(3):
            self.file.append(FileStorage())
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Chỉ được upload 1 file 1 lần'
