# coding=utf-8
import os

import config
import unittest
from mock import patch

import pytest

from catalog.biz.product_import import update_editing_status_for_sellables
from catalog.biz.product_import.import_update_seo_info import update_seo_info_for_sellables
from catalog.extensions.flask_cache import cache
from catalog.services.imports.file_import import ImportFileUpdateEditingStatus
from catalog.models import SellableProduct
import catalog.models as m
from tests import logged_in_user
from tests.faker import fake
from tests.utils import JiraTest


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


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
class ImportUpdateProductStatusTestCase(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-830'
    FOLDER = '/Import/UpdateSeoInfo'

    def setUp(self):
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.import_type = ImportFileUpdateEditingStatus.IMPORT_FILE_TYPE
        fake.init_editing_status()
        skus = ['123', '124', '125']
        seller_skus = ['123', '124', '124']
        uom_codes = ['CHIEC', 'HOP', 'LOC']
        uom_ratios = [1, 1, 4]
        self.sellable_products = [fake.sellable_product(
            sku=skus[i],
            seller_sku=seller_skus[i],
            uom_code=uom_codes[i],
            uom_ratio=uom_ratios[i],
            seller_id=self.seller.id,
            terminal_id='0'
        ) for i in range(3)]

        self.sellable_update_signal_patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.mock_sellable_create_signal = self.sellable_update_signal_patcher.start()

        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.create_product_basic_info.app.request_context')
        self.mock_app_request_context = self.app_request_context_patcher.start()

        self.requests_post_patcher = patch(
            'catalog.biz.product_import.requests.post')

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

    def test_backgroundJob_upsertSeoInfo(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(
                config.ROOT_DIR,
                "tests/storage/template/import_update_seo_info/template_import_update_seo_info_success.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            update_seo_info_for_sellables(params={
                'id': file_import.id
            })

        db_sellable = SellableProduct.query.filter(
            SellableProduct.sku == '123'
        ).first()
        product = m.Product.query.filter(m.Product.id == db_sellable.product_id).first()

        assert product.display_name == 'seoname'
        assert product.meta_title == 'metatitle'
        assert product.meta_keyword == 'metakeyword'
        assert product.meta_description == 'metadescription'
        assert product.url_key == 'slug'

        db_sellable = SellableProduct.query.filter(
            SellableProduct.sku == '124'
        ).first()
        product = m.Product.query.filter(m.Product.id == db_sellable.product_id).first()

        assert product.display_name == 'seoname2'
        assert product.meta_title == 'metatitle2'
        assert product.meta_keyword == 'metakeyword2'
        assert product.meta_description == 'metadescription2'
        assert product.url_key == 'slug2'

    def test_backgroundJob_foundMultipleResultForOneSellerSku_showErrorRequestInputUom(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(
                config.ROOT_DIR,
                "tests/storage/template/import_update_seo_info/template_import_update_seo_info_found_multiple_result_for_one_seller_sku.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_result = update_seo_info_for_sellables(params={
                'id': file_import.id
            })

        assert import_result[0] == 'Không tìm được sản phẩm với sku tương ứng, vui lòng nhập chính xác uom và uom_ratio để tìm đúng sản phẩm'

    def test_backgroundJob_updateFailCannotFindSellerSku(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(
                config.ROOT_DIR,
                "tests/storage/template/import_update_seo_info/template_import_update_seo_info_cannot_find_seller_sku.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_result = update_seo_info_for_sellables(params={
                'id': file_import.id
            })

        assert import_result[0] == 'Sản phẩm không tồn tại'
