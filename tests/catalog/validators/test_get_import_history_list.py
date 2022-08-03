#coding=utf-8

from datetime import (
    datetime,
    timedelta
)

import pytest

from catalog.validators.imports import ImportHistoryListValidator
from catalog.api.imports import schema
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake


TIME_FMT = '%d/%m/%Y'

class GetImportHistoryListTestCase(APITestCase):
    ISSUE_KEY = 'SC-459'

    def setUp(self):
        self.data = {}

    def run_validator(self):
        data = schema.FileImportHistoryListParam().load(self.data)
        ImportHistoryListValidator.validate({
            'data': data
        })

    def test_passValidData__allowPass(self):
        self.run_validator()

    def test_passStartAtGreaterThanNow__raiseBadRequestException(self):
        self.data['startAt'] = (datetime.now() + timedelta(days=2)).strftime(TIME_FMT)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'startAt phải trước thời điểm hiện tại'

    def test_passStartAtGreaterThanEndAt__raiseBadRequestException(self):
        a = datetime.now()
        self.data['startAt'] = (a + timedelta(days=1)).strftime(TIME_FMT)
        self.data['endAt'] = a.strftime(TIME_FMT)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'startAt phải trước thời điểm endAt'

    def test_passStatusInvalid__raiseBadRequestException(self):
        self.data['status'] = fake.text()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'status không hợp lệ'

    def test_passImportTypeInvalid__raiseBadRequestException(self):
        self.data['type'] = fake.text()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'type không hợp lệ'
