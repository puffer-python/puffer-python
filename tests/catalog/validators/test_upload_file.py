# coding=utf-8

import io

import pytest
import pandas as pd
import numpy as np
from werkzeug.datastructures import (
    FileStorage,
    ImmutableMultiDict,
)

from config import MAX_IMPORT_FILE_PENDING
from catalog.validators.imports import UploadFileImportProductValidator, UploadFileValidator, \
    UploadFileUpdateProductTagValidator
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake

TITLE_ROW_OFFSET = 1


class VersionValidatorTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-527'
    FOLDER = '/Import/Upload'

    def setUp(self):
        out = io.BytesIO()
        df = pd.DataFrame(data=[1], index=[1], columns=['A']).to_excel(out, sheet_name='VERSION', index=False, header=False)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )
        self.import_type_list = [
            'create_product',
            'create_product_basic_info',
            'tag_product',
            'update_editing_status',
            'update_product',
            'update_terminal_groups',
            'update_attribute_product'
        ]

    def tearDown(self):
        UploadFileValidator.IMPORT_TYPE_CODE = ''

    def run_validator(self, import_type):
        files = ImmutableMultiDict({'file': self.file})
        UploadFileValidator.IMPORT_TYPE_CODE = import_type
        UploadFileValidator().validate_version(files)

    def test_200_rightVersion(self):
        for import_type in self.import_type_list:
            fake.misc(data_type='import_type', code=import_type, config='{"version":1}')
            self.run_validator(import_type)

    def test_400_wrongVersion(self):
        for import_type in self.import_type_list:
            fake.misc(data_type='import_type', code=import_type, config='{"version":2}')
            with pytest.raises(exc.BadRequestException) as error_info:
                self.run_validator(import_type)
            assert error_info.value.message == 'Mẫu file import của bạn đã cũ. Vui lòng tải lại file mẫu mới để thực hiện'

    def test_200_notDBVersionAndNotImportVersion(self):
        out = io.BytesIO()
        df = pd.DataFrame(data=[1], index=[1], columns=['A']).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )

        for import_type in self.import_type_list:
            fake.misc(data_type='import_type', code='tag_product')
            self.run_validator(import_type)

    def test_200_notDBVersionAndImportVersion(self):
        for import_type in self.import_type_list:
            fake.misc(data_type='import_type', code='tag_product')
            self.run_validator(import_type)

    def test_400_DBVersionAndNotImportVersion(self):
        out = io.BytesIO()
        df = pd.DataFrame(data=[1], index=[1], columns=['A']).to_excel(out)
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )

        for import_type in self.import_type_list:
            fake.misc(data_type='import_type', code=import_type, config='{"version":1}')
            with pytest.raises(exc.BadRequestException) as error_info:
                self.run_validator(import_type)
            assert error_info.value.message == 'Mẫu file import của bạn đã cũ. Vui lòng tải lại file mẫu mới để thực hiện'

