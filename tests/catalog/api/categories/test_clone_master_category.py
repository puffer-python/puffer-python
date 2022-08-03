from unittest.mock import patch

from catalog import models
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class CloneMasterCategory(APITestCase):
    ISSUE_KEY = 'CATALOGUE-372'
    FOLDER = '/Category/Clone'

    def url(self):
        return '/categories/clone_from_master_categories'

    def method(self):
        return 'POST'

    def __create_category(self, number_of_category, category_type, is_root=False, parent_categories=[]):
        if not isinstance(parent_categories, list):
            parent_categories = [parent_categories]

        categories = []
        fake_category = getattr(fake, category_type)
        if is_root:
            for i in range(number_of_category):
                categories.append(fake_category(
                    is_active=True,
                    parent_id=0,
                    seller_id=self.seller.id,
                ))
        else:
            for category in parent_categories:
                for i in range(number_of_category):
                    categories.append(fake_category(
                        is_active=True,
                        parent_id=category.id,
                        seller_id=self.seller.id,
                    ))

        return categories

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.master_categories_level_0 = self.__create_category(
            number_of_category=2, category_type='master_category', is_root=True)
        self.master_categories_level_1 = self.__create_category(
            number_of_category=1, parent_categories=self.master_categories_level_0[0], category_type='master_category')
        self.master_categories_level_2 = self.__create_category(
            number_of_category=1, parent_categories=self.master_categories_level_1, category_type='master_category')
        self.master_categories_level_3 = self.__create_category(
            number_of_category=1, parent_categories=self.master_categories_level_2, category_type='master_category')

        self.inactive_master_categories = [
            fake.master_category(is_active=False, parent_id=0, seller_id=self.seller.id).id
            for _ in range(2)
        ]

        self.payload = {
            "sellerId": self.seller.id
        }

    @patch('catalog.extensions.signals.clone_master_category_request_signal.send')
    def test_200_cloneAListOfMasterCategoryIds(self, mock):
        mock.return_value = None
        self.payload['masterCategoryIds'] = [
            self.master_categories_level_0[0].id, self.master_categories_level_0[1].id]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], "Nhận yêu cầu thành công")

    def test_400_notTopLevelMasterCategoryIds(self):
        self.payload['masterCategoryIds'] = [
            self.master_categories_level_0[0].id, self.master_categories_level_1[0].id]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(
                body['message'],
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {[self.master_categories_level_1[0].id]}')

    def test_400_allNotExistMasterCategoryIdsInList(self):
        self.payload['masterCategoryIds'] = [
            self.master_categories_level_0[0].id, 123]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(
                body['message'],
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {[123]}')

    def test_400_anNotExistMasterCategoryIdInList(self):
        self.payload['masterCategoryIds'] = [123, 456]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(
                body['message'],
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {[123, 456]}')

    def test_400_invalidMasterCategoryIds(self):
        self.payload['masterCategoryIds'] = [
            self.master_categories_level_0[0].id, 'string']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)

    def test_400_anInactiveMasterCategoryIdInList(self):
        self.payload['masterCategoryIds'] = [self.inactive_master_categories[0]]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(
                body['message'],
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {[self.inactive_master_categories[0]]}'
            )

    def test_400_allInactiveMasterCategoryIdsInList(self):
        self.payload['masterCategoryIds'] = [
                                                self.master_categories_level_0[0].id
                                            ] + self.inactive_master_categories

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(
                body['message'],
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {self.inactive_master_categories}'
            )

    def test_400_emptyListMasterCategoryIds(self):
        self.payload['masterCategoryIds'] = []

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)

    def test_400_fieldMasterCategoryIdIsNone(self):
        self.payload['masterCategoryIds'] = None

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)

    def test_400_notFoundFieldMasterCategoryIds(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)

    @patch('catalog.services.seller.get_seller_by_id')
    def test_400_notExistSellerId(self, mock):
        self.payload = {
            'masterCategoryIds': [self.master_categories_level_0[0].id],
            'sellerId': 123
        }
        mock.return_value = {}

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Seller không tồn tại')

    def test_400_notFoundFieldSellerId(self):
        self.payload = {
            'masterCategoryIds': [self.master_categories_level_0[0].id],
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload)
            self.assertEqual(code, 400)
