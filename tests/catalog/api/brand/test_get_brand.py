# coding=utf-8
import logging
from datetime import datetime
import urllib.parse as parse

import pytest

from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class TestGetBrand(APITestCase):
    def setUp(self):
        self.brand = fake.brand()

    def url(self):
        return '/brands/{}'

    def method(self):
        return 'GET'

    def assert_brand_data(self, brand, data):
        for key, value in data.items():
            if hasattr(brand, key):
                if key == 'path':
                    if value is not None:
                        url = parse.urlparse(value)
                        value = url.path

                elif key in ('created_at', 'updated_at'):
                    value = datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
                self.assertEqual(value, getattr(brand, key))

    def test_getBrandExisted__returnCorrectInfo(self):
        url = self.url().format(self.brand.id)
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_brand_data(self.brand, body['result'])

    def test_getBrandNotExist__returnInvalidResponse(self):
        url = self.url().format(999999999)
        code, _ = self.call_api(url=url)

        self.assertEqual(400, code)

    def test_passBrandIdNull__returnInvalidResponse(self):
        url = self.url().format('null')
        code, _ = self.call_api(url=url)
        assert 404 == code
