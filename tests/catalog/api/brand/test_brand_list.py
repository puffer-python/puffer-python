# coding=utf-8
import logging

from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class BrandListTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-406'
    FOLDER = '/Brand/GetList'

    def setUp(self):
        super().setUp()
        self.brands = [fake.brand() for _ in range(20)]
        self.page = 1
        self.page_size = 10

    def method(self):
        return 'GET'

    def url(self):
        return '/brands'

    def query_with(self, params):
        query_params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        if 'page' not in params:
            query_params = f'{query_params}&page={self.page}'
        if 'pageSize' not in params:
            query_params = f'{query_params}&pageSize={self.page_size}'
        url = f'{self.url()}?{query_params}'

        code, body = self.call_api(url=url, method=self.method())

        return (code, body['result']['brands']) if code == 200 else (code, body)

    def test_passValidBrandName__returnExactBrand(self):
        brand = self.brands[0]
        code, brands = self.query_with({
            'query': brand.name
        })

        self.assertEqual(200, code)
        self.assertEqual(brand.id, brands[0]['id'])
        self.assertEqual(brand.name, brands[0]['name'])

    def test_passValidBrandCode__returnExactBrand(self):
        brand = self.brands[0]
        code, brands = self.query_with({
            'codes': brand.code
        })

        self.assertEqual(brand.id, brands[0]['id'])
        self.assertEqual(brand.code, brands[0]['code'])

    def test_passRandomQueryParam__returnNothing(self):
        code, brands = self.query_with({
            'query': 'Tên này không tồn tại'
        })

        self.assertEqual(200, code)
        self.assertEqual(0, len(brands))

    def test_passPaginationParams__returnCorrectNumberOfItems(self):
        """
        Check if pagination works correctly
        :return:
        """

        def calculate_item_in_page(page, page_size, total):
            remains = total - (page - 1) * page_size

            return remains if remains <= page_size else page_size

        page = 4
        page_size = 3

        code, brands = self.query_with({
            'page': page,
            'pageSize': page_size
        })

        self.assertEqual(200, code)
        self.assertEqual(
            len(brands),
            calculate_item_in_page(
                page,
                page_size,
                20
            )
        )

    def test_isActiveNotBooleanValue__returnInvalidResponse(self):
        code, _ = self.query_with({'isActive': 'sds'})

        self.assertEqual(400, code)

    def test_pageOutOfRange__returnInvalidResponse(self):
        code, _ = self.query_with({'page': 100000000000000})

        self.assertEqual(400, code)

    def test_pageNegative__returnInvalidResponse(self):
        code, _ = self.query_with({'page': -1})

        self.assertEqual(400, code)

    def test_notPassingPageParam__returnInvalidResponse(self):
        code, _ = self.call_api()

        self.assertEqual(200, code)

    def test_pageSizeEqualsZero__returnEmptyResponse(self):
        code, brands = self.query_with({'pageSize': 0})

        self.assertEqual(400, code)

    def test_approvedStatusNotBoolean__returnInvalidResponse(self):
        code, _ = self.query_with({'approvedStatus': 'sdd'})

        self.assertEqual(400, code)

    def test_200_hasLogoIsFalse(self):
        brand = fake.brand(hasLogo=False)
        code, brands = self.query_with({
            'hasLogo': 0
        })

        self.assertEqual(200, code)
        self.assertEqual(len(brands), 1)
        self.assertEqual(brand.id, brands[0]['id'])
        self.assertEqual(brand.name, brands[0]['name'])

    def test_200_missingHasLogo(self):
        fake.brand(hasLogo=False)
        code, brands = self.query_with({
            'pageSize': 30
        })

        self.assertEqual(200, code)
        self.assertEqual(len(brands), 21)

    def test_200_hasLogoIsTrue(self):
        fake.brand(hasLogo=False)
        code, brands = self.query_with({
            'hasLogo': 1,
            'pageSize': 30
        })

        self.assertEqual(200, code)
        self.assertEqual(len(brands), 20)
