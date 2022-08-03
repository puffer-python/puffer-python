# coding=utf-8
from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog.api.category import schema


class GetListCategoriesTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1131'
    FOLDER = '/Category/getListCategories/Platform'

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
            self.other_categories_1.append(
                fake.category(seller_id=self.seller_1.id, master_category_id=self.master_category.id))
        for _ in range(10):
            self.other_categories_2.append(
                fake.category(seller_id=self.seller_2.id, master_category_id=self.master_category.id))

    def get_url(self, platform_id):
        if platform_id:
            return '/categories?platformId=' + str(platform_id) + '&page={}&pageSize={}'
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

    def test_list_categories_return_200_with_platform_id_param_that_seller_own(self):
        with logged_in_user(self.user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = self.seller.id
                page = 1
                page_size = 10
                url = self.get_url(1).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                self.assertCategories(self.categories, body['result']['categories'])

    def test_list_categories_return_200_with_platform_id_param_that_seller_not_owner(self):
        with logged_in_user(self.user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = self.seller_2.id
                page = 1
                page_size = 10
                url = self.get_url(1).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                self.assertCategories(self.other_categories_2, body['result']['categories'])

    def test_list_categories_return_200_without_platform_id_param_has_default_platform(self):
        with logged_in_user(self.user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = None
                page = 1
                page_size = 10
                url = self.get_url(None).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                self.assertCategories(self.categories, body['result']['categories'])

    def test_list_categories_return_200_date_belong_this_seller_without_platform_id_param_and_no_default_platform(self):
        with logged_in_user(self.user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = None
                page = 1
                page_size = 10
                url = self.get_url(None).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                self.assertCategories(self.categories, body['result']['categories'])

    def test_list_categories_return_200_empty_data_without_platform_id_param_and_no_default_platform(self):
        new_seller = fake.seller()
        new_user = fake.iam_user(seller_id=new_seller.id)
        with logged_in_user(new_user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = None
                page = 1
                page_size = 10
                url = self.get_url(None).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                assert body['result']['totalRecords'] == 0
                assert len(body['result']['categories']) == 0

    def test_list_categories_return_200_empty_data_without_platform_id_param_and_no_assigned_platforms(self):
        new_seller = fake.seller()
        new_user = fake.iam_user(seller_id=new_seller.id)
        with logged_in_user(new_user):
            with patch('catalog.services.seller.get_platform_owner') as mock_response:
                mock_response.return_value = self.seller.id
                page = 1
                page_size = 10
                url = self.get_url(None).format(page, page_size)
                code, body = self.call_api(url=url)
                assert body['result']['currentPage'] == page
                assert body['result']['pageSize'] == page_size
                assert body['result']['totalRecords'] == 0
                assert len(body['result']['categories']) == 0
