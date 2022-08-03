# coding=utf-8
import logging
import os

from mock import patch
from catalog.extensions.flask_cache import cache
import config
from catalog import models as m
from catalog.biz.product_import.import_upsert_product_category import upsert_product_categories
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'quang.lm'
_logger = logging.getLogger(__name__)


class MockResponse:
    def __init__(self, status_code, headers=None, content=None, url=None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.url = url

    def json(self):
        return {
            'url': self.url
        }


class TestImportUpdateProductCategories(APITestCase):
    ISSUE_KEY = "CATALOGUE-1129"
    FOLDER = "Product/Import/PlatformCategories"

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.platform_id = 1
        fake.platform_sellers(platform_id=self.platform_id, seller_id=self.seller.id, is_default=True,
                              is_owner=True)

        self.sellable_update_signal_patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.mock_sellable_create_signal = self.sellable_update_signal_patcher.start()

        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.import_upsert_product_category.app.request_context')
        self.mock_app_request_context = self.app_request_context_patcher.start()
        self.requests_post_patcher = patch(
            'catalog.biz.product_import.import_upsert_product_category.requests.post')

        self.mock_requests_post = self.requests_post_patcher.start()
        self.mock_requests_post.return_value = MockResponse(
            status_code=200,
            url='url_xlsx_test',
        )
        cache.clear()

    def tearDown(self):
        self.sellable_update_signal_patcher.stop()
        self.app_request_context_patcher.stop()
        self.requests_post_patcher.stop()
        cache.clear()

    def __mock_get_data(self, mock_get_data, seller_sku, category_id):
        mock_get_data.return_value = ({0: (seller_sku, category_id)}, [seller_sku], [category_id])

    def __import(self, platform_id=None):
        with logged_in_user(self.user):
            file_stream = os.path.join(
                config.ROOT_DIR,
                'tests/storage/template',
                'template_upsert_product_category.xlsx'
            )
            file_import = fake.file_import(
                user_info=self.user,
                type='import_upsert_product_category',
                status='new',
                path=file_stream,
                set_id=None,
                total_row_success=0
            )
            return upsert_product_categories(
                params={'id': file_import.id, 'platform_id': platform_id or self.platform_id})

    def __add_sku(self, seller_sku, seller_id, category_id=None):
        sku = fake.sellable_product(seller_sku=seller_sku, seller_id=seller_id, category_id=category_id)
        self._add_product_category(sku.product_id, sku.category_id)
        return sku

    def _add_product_category(self, product_id, category_id):
        product_category = m.ProductCategory()
        product_category.product_id = product_id
        product_category.category_id = category_id
        product_category.created_by = 'system'
        m.db.session.add(product_category)
        m.db.session.commit()

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_missing_seller_sku(self, mock_get_data):
        mock_get_data.return_value = ({0: (None, 1)}, [], [1])
        import_result = self.__import()
        self.assertEqual('Chưa nhập seller sku', import_result[0])

    def test_import_error_with_seller_sku_not_exists(self):
        import_result = self.__import()
        self.assertEqual('Sản phẩm không tồn tại', import_result[0])
        self.assertEqual('Sản phẩm không tồn tại', import_result[1])

    def test_import_error_with_seller_sku_not_belong_to_seller(self):
        seller = fake.seller()
        self.__add_sku('123456', seller.id)
        self.__add_sku('234567', seller.id)
        import_result = self.__import()
        self.assertEqual('Sản phẩm không tồn tại', import_result[0])
        self.assertEqual('Sản phẩm không tồn tại', import_result[1])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_missing_category(self, mock_get_data):
        mock_get_data.return_value = ({0: ('123456', None)}, ['123456'], [])
        import_result = self.__import()
        self.assertEqual('Chưa nhập danh mục ngành hàng', import_result[0])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_category_not_exists(self, mock_get_data):
        self.__add_sku('123456', self.seller.id)
        categories = m.Category.query.all()
        not_found_category_id = max(map(lambda x: x.id, categories)) + 1
        self.__mock_get_data(mock_get_data, '123456', not_found_category_id)
        import_result = self.__import()
        self.assertEqual('Danh mục ngành hàng không tồn tại', import_result[0])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_category_not_active(self, mock_get_data):
        self.__add_sku('123456', self.seller.id)
        not_active_category = fake.category(is_active=False, seller_id=self.seller.id)
        self.__mock_get_data(mock_get_data, '123456', not_active_category.id)
        import_result = self.__import()
        self.assertEqual('Danh mục ngành hàng bị vô hiệu', import_result[0])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_category_not_leaf(self, mock_get_data):
        self.__add_sku('123456', self.seller.id)
        root_category = fake.category(seller_id=self.seller.id)
        fake.category(seller_id=self.seller.id, parent_id=root_category.id)
        self.__mock_get_data(mock_get_data, '123456', root_category.id)
        import_result = self.__import()
        self.assertEqual('Danh mục ngành hàng phải là lá', import_result[0])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_error_with_category_not_belong_to_platform(self, mock_get_data):
        seller = fake.seller()
        self.__add_sku('123456', self.seller.id)
        category = fake.category(seller_id=seller.id)
        self.__mock_get_data(mock_get_data, '123456', category.id)
        import_result = self.__import()
        self.assertEqual('Danh mục không thuộc sàn', import_result[0])

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_success_with_update_platform_category(self, mock_get_data):
        current_category = fake.category(seller_id=self.seller.id)
        sku = self.__add_sku('123456', self.seller.id, category_id=current_category.id)
        product_id = sku.product_id
        category = fake.category(seller_id=self.seller.id)
        category_id = category.id
        self.__mock_get_data(mock_get_data, '123456', category_id)
        import_result = self.__import()
        product_category = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id,
                                                          m.ProductCategory.category_id == category_id).first()
        self.assertEqual('Thành công', import_result[0])
        self.assertIsNotNone(product_category)

    @patch('catalog.biz.product_import.import_upsert_product_category.get_data_from_file')
    def test_import_success_with_insert_platform_category(self, mock_get_data):
        current_category = fake.category(seller_id=self.seller.id)
        sku = self.__add_sku('123456', self.seller.id, category_id=current_category.id)
        product_id = sku.product_id
        seller = fake.seller()
        fake.platform_sellers(platform_id=2, seller_id=seller.id, is_default=True,
                              is_owner=True)
        category = fake.category(seller_id=seller.id)
        category_id = category.id
        self.__mock_get_data(mock_get_data, '123456', category_id)
        import_result = self.__import(platform_id=2)
        product_category = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id,
                                                          m.ProductCategory.category_id == category_id).first()
        self.assertEqual('Thành công', import_result[0])
        self.assertIsNotNone(product_category)
