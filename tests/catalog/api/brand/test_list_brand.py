# coding=utf-8
import logging
from datetime import datetime
import urllib.parse as parse
import random


from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class TestListBrandByIds(APITestCase):
    ISSUE_KEY = 'CATALOGUE-795'
    FOLDER = '/Band/List'

    def setUp(self):
        self.brands = [fake.brand(), fake.brand(), fake.brand(), fake.brand(), fake.brand()]
        self.brands.sort(key=lambda x: x.updated_at, reverse=True)

    def url(self):
        return '/brands?ids={}'

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

    def test_list_brands_return200__all_brands_with_empty_ids(self):
        url = self.url().format('')
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual(len(self.brands), body['result']['totalRecords'])
        self.assertEqual(len(self.brands), len(body['result']['brands']))
        for i in range(len(self.brands)):
            self.assert_brand_data(self.brands[i], body['result']['brands'][i])

    def test_list_brands_return200__multiple_brands(self):
        ids = str.join(', ', map(lambda x: str(x.id), self.brands))
        url = self.url().format(f'{ids}')
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual(len(self.brands), body['result']['totalRecords'])
        self.assertEqual(len(self.brands), len(body['result']['brands']))
        for i in range(len(self.brands)):
            self.assert_brand_data(self.brands[i], body['result']['brands'][i])

    def test_list_brands_return200__only_one_brand(self):
        brand = random.choice(self.brands)
        url = self.url().format(f'{brand.id}')
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual(1, body['result']['totalRecords'])
        self.assertEqual(1, len(body['result']['brands']))
        self.assert_brand_data(brand, body['result']['brands'][0])

    def test_list_brands_return200__no_brands(self):
        not_found_brand_id = max(map(lambda x: x.id, self.brands)) + 1
        url = self.url().format(f'{not_found_brand_id}')
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual(0, body['result']['totalRecords'])
        self.assertEqual(0, len(body['result']['brands']))
