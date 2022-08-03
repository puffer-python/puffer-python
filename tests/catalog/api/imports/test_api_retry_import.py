# coding=utf-8

import json
import logging
from mock import patch
from catalog import models as m
import config
from catalog.services.categories import CategoryService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class RetryImportResultTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-364'
    FOLDER = '/Import/Retry'

    def url(self):
        return '/import/retry/{}'.format(self.his_id)

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.user = fake.iam_user()
        records = [fake.file_import(user_info=self.user) for _ in range(3)]
        self.his = fake.random_element(records)
        self.his_id = self.his.id
        result_imports = [fake.result_import(file_import=self.his) for _ in range(5)]

    def test_retry_import_result_successful_return200(self):
        body = {
            "saveOnly": False,
            "items": [{
                "data": {
                    "image": "",
                    "name": "",
                },
                "id": 1
            }]
        }
        with logged_in_user(self.user):
            code, rbody = self.call_api(data=body)
        assert code == 200
        assert rbody
        assert len(body['items']) == len(rbody['result'])

    def test_retry_import_result_successful_with_failed_rows_return200(self):
        body = {
            "saveOnly": False,
            "items": [{
                "data": {
                    "image": "",
                    "name": "",
                },
                "id": 1
            }]
        }
        with logged_in_user(self.user):
            code, rbody = self.call_api(data=body)
        assert code == 200
        assert rbody
        assert len(body['items']) == len(rbody['result'])

    def test_retry_import_result_lack_saveOnly_return400_InvalidParameter(self):
        body = {
            "items": [{
                "data": {
                    "image": "",
                    "name": "",
                },
                "id": 1
            }]
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=body)
        assert code == 400
        assert body

    def test_retry_import_result_lack_items_return400_InvalidParameter(self):
        rows = m.db.session.query(m.ResultImport).all()
        body = {
            "saveOnly": False
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=body)
        assert code == 400
        assert body

    def test_retry_import_result_empty_items_return400_InvalidParameter(self):
        body = {
            "saveOnly": False,
            "items": []
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=body)
        assert code == 400
        assert body

    def test_retry_import_result_saveOnly_true_return200(self):
        body = {
            "saveOnly": True,
            "items": [{
                "data": {
                    "image": "",
                    "name": "",
                },
                "id": 1
            }]
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=body)
        assert code == 200
        assert body

    def test_retry_import_result_saveOnly_false_return200(self):
        body = {
            "saveOnly": False,
            "items": [{
                "data": {
                    "image": "",
                    "name": "",
                },
                "id": 1
            }]
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=body)
        assert code == 200
        assert body
