# coding=utf-8
import json

import pytest
import requests
from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog.api.category import schema


def _mock_get_platform(seller_id):
    data = {
        "code": "200",
        "message": "OK",
        "result": {
            "platforms": [
                {
                    "id": 1,
                    "brand": "string",
                    "name": "string",
                    "code": "string",
                    "dealerCanEditAddress": 0,
                    "allowUserEditAddress": True,
                    "dealerRequestRequireApproval": 0,
                    "allowUserResgistration": True,
                    "ownerSellerId": seller_id,
                    "paymentMerchantCode": "string",
                    "isDefault": True
                }
            ],
            "page": 0,
            "pageSize": 0,
            "total": 0
        }
    }
    return json.dumps(data).encode('utf8')


class GetListCategoriesTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-351'
    FOLDER = '/Category/getListCategories'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )

        self.categories = list()
        for _ in range(12):
            self.categories.append(fake.category(seller_id=self.seller.id, master_category_id=self.master_category.id))
        self.categories.append(fake.category(seller_id=self.seller.id))
        self.other_category = fake.category()

    def url(self):
        return '/categories?page={}&pageSize={}'

    def method(self):
        return 'GET'

    def assertCategories(self, categories, categories_data):
        assert len(categories) == len(categories_data)

        categories_real = schema.CategoryGenericForList(many=True).dump(categories)
        categories_data = sorted(categories_data, key=lambda item: item['code'])
        categories_real = sorted(categories_real, key=lambda item: item['code'])
        for real, data in zip(categories_real, categories_data):
            for key, value in data.items():
                assert value == real[key]
            category = models.Category.query.get(data['id'])

            self.assertTrue('masterCategory' in data)
            if data['masterCategory']:
                assert data['masterCategory']['id'] == self.master_category.id
                assert data['masterCategory']['path'] == self.master_category.path
                assert category.master_category_id == self.master_category.id
            else:
                self.assertIsNone(data['masterCategory'])
                self.assertIsNone(category.master_category_id)

    @patch('catalog.services.categories.category.CategoryService.get_list_categories')
    def test_getMappedMasterCategory_200_returnSuccessfully(self, mock):
        page = 1
        page_size = 10
        mock.return_value = (self.categories[:page_size], len(self.categories))
        with logged_in_user(self.user):
            url = self.url().format(page, page_size)
            code, body = self.call_api(url=url)
            assert body['result']['currentPage'] == page
            assert body['result']['pageSize'] == page_size
            self.assertCategories(self.categories[:10], body['result']['categories'])

    @patch('catalog.services.categories.category.CategoryService.get_list_categories')
    def test_getUnMappedMasterCategories_200_returnSuccessfully(self, mock):
        self.categories = list()
        for _ in range(10):
            self.categories.append(fake.category(seller_id=self.seller.id))
        self.categories.append(fake.category(seller_id=self.seller.id))

        page = 1
        page_size = 10
        mock.return_value = (self.categories[page_size:], len(self.categories))
        with logged_in_user(self.user):
            url = self.url().format(page, page_size)
            code, body = self.call_api(url=url)
            assert body['result']['currentPage'] == page
            assert body['result']['pageSize'] == page_size
            self.assertCategories(self.categories[10:], body['result']['categories'])


class GetListCategoriesFilterBySellersTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-627'
    FOLDER = '/Category/getListCategories'

    def setUp(self):
        self.seller = fake.seller()
        self.seller_1 = fake.seller()
        self.seller_2 = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )

        self.categories = list()
        self.other_categories_1 = list()
        self.other_categories_2 = list()
        for _ in range(10):
            self.categories.append(fake.category(seller_id=self.seller.id, master_category_id=self.master_category.id))
        for _ in range(10):
            self.other_categories_1.append(fake.category(seller_id=self.seller_1.id))
        for _ in range(10):
            self.other_categories_2.append(fake.category(seller_id=self.seller_2.id))

    def url(self):
        return '/categories?page={}&pageSize={}'

    def urlWithSellerIds(self):
        return self.url() + '&sellerIds={}'

    def method(self):
        return 'GET'

    def test_getCategoriesWithSellerIdEqual0_200_returnCategoriesOfAllSellers(self):
        page = 1
        page_size = 30
        with logged_in_user(self.user):
            url = self.urlWithSellerIds().format(page, page_size, 0)
            code, body = self.call_api(url=url)
            assert code == 200
            assert body['result']['currentPage'] == page
            assert body['result']['pageSize'] == page_size
            assert len(body['result']['categories']) == len(self.categories) + len(self.other_categories_1) + len(
                self.other_categories_2)
            assert body['result']['totalRecords'] == len(self.categories) + len(self.other_categories_1) + len(
                self.other_categories_2)

    def test_getCategoriesWithSellerIdEquaListMultipleSellers_200_returnCategoriesOfSelectedSellers(self):
        page = 1
        page_size = 30
        with logged_in_user(self.user):
            url = self.urlWithSellerIds().format(page, page_size,
                                                 "{},{}".format(self.seller_1.id, self.seller_2.id))
            code, body = self.call_api(url=url)
            assert code == 200
            assert body['result']['currentPage'] == page
            assert body['result']['pageSize'] == page_size
            assert len(body['result']['categories']) == len(self.other_categories_1) + len(self.other_categories_2)
            assert body['result']['totalRecords'] == len(self.other_categories_1) + len(self.other_categories_2)

    def test_getCategoriesWithOutSellerIdParameter_200_returnCategoriesForUserSellerOnly(self):
        page = 1
        page_size = 30
        with logged_in_user(self.user):
            url = self.url().format(page, page_size)
            code, body = self.call_api(url=url)
            assert code == 200
            assert body['result']['currentPage'] == page
            assert body['result']['pageSize'] == page_size
            assert len(body['result']['categories']) == len(self.categories)
            assert body['result']['totalRecords'] == len(self.categories)


class GetListCategoriesShippingTypesTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1106'
    FOLDER = '/Category/getListCategories/shippingTypes'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )

        self.categories = list()
        for _ in range(10):
            self.categories.append(fake.category(seller_id=self.seller.id, master_category_id=self.master_category.id))

    def url(self):
        return '/categories?page=1&pageSize=10'

    def method(self):
        return 'GET'

    def test__200__returnNoShippingType(self):
        with logged_in_user(self.user):
            url = self.url() + '&ids=' + str(self.categories[0].id)
            code, body = self.call_api(url=url)
            self.assertEqual(code, 200)
            self.assertEqual(len(body['result']['categories'][0]['shippingTypes']), 0)

    def test__200__returnOnlyOneShippingType(self):
        expect_shipping_type = fake.shipping_type()
        fake.category_shipping_type(self.categories[0].id, expect_shipping_type.id)

        with logged_in_user(self.user):
            url = self.url() + '&ids=' + str(self.categories[0].id)
            code, body = self.call_api(url=url)
            self.assertEqual(code, 200)
            result = body['result']['categories'][0]
            self.assertEqual(len(result['shippingTypes']), 1)
            self.assertEqual(result['shippingTypes'][0]['id'], expect_shipping_type.id)
            self.assertEqual(result['shippingTypes'][0]['code'], expect_shipping_type.code)
            self.assertEqual(result['shippingTypes'][0]['name'], expect_shipping_type.name)

    def test__200__returnMultipleShippingTypes(self):
        expect_shipping_types = [fake.shipping_type() for _ in range(2)]
        for shipping_type in expect_shipping_types:
            fake.category_shipping_type(self.categories[0].id, shipping_type.id)

        with logged_in_user(self.user):
            url = self.url() + '&ids=' + str(self.categories[0].id)
            code, body = self.call_api(url=url)
            self.assertEqual(code, 200)
            result = body['result']['categories'][0]['shippingTypes']
            self.assertEqual(len(result), 2)
            for i in range(2):
                self.assertIn(result[i]['id'], [shipping_type.id for shipping_type in expect_shipping_types])
                self.assertIn(result[i]['code'], [shipping_type.code for shipping_type in expect_shipping_types])
                self.assertIn(result[i]['name'], [shipping_type.name for shipping_type in expect_shipping_types])
