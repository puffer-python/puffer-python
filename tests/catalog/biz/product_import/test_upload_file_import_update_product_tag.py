# coding=utf-8
import os
import config
import unittest
from copy import deepcopy

from mock import patch

import pytest

from catalog.biz.product_import import update_tag_for_sellable_products
from catalog.extensions.flask_cache import cache
from catalog.services.imports.file_import import ImportFileUpdateProductTag
from catalog.models import SellableProductTag
from catalog import models as m
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
class ImportUpdateProductTagTestCase(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-626'
    FOLDER = '/Import/Update_product_tag'

    def setUp(self):
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.import_type = ImportFileUpdateProductTag.IMPORT_FILE_TYPE
        skus = ['123','124','125', '00234']
        seller_skus = ['123', '124', '124', '00234']
        uom_codes = ['CHIEC', 'HOP', 'LOC', 'PACK']
        uom_ratios = [1, 1, 4, 6]
        self.sellable_products = [fake.sellable_product(
            sku=skus[i],
            seller_sku=seller_skus[i],
            uom_code=uom_codes[i],
            uom_ratio=uom_ratios[i],
            editing_status_code='active',
            seller_id=self.seller.id
        ) for i in range(len(skus)) ]

        self.sku_ids = [sku.id for sku in self.sellable_products]

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

    def test_backgroundJob_importUpdateProductTag__update_successfully_with_seller_sku_field_only(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/import_update_product_tag/template_update_product_tag_success_with_sku_only.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            result = update_tag_for_sellable_products(params={
                'id': file_import_id
            })
            m.db.session.commit()
            result_import = m.FileImport.query.get(file_import_id)
            self.assertEqual(result_import.status, 'done')
            db_sellable_tag = SellableProductTag.query.all()
            self.assertEqual(len(db_sellable_tag), 2)
            self.assertEqual(db_sellable_tag[0].tags, 'tag1', result)
            self.assertEqual(db_sellable_tag[1].tags, 'tag2', result)


    def test_backgroundJob_importUpdateProductTag__update_successfully_with_seller_sku_uom_and_uomRatio(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/import_update_product_tag/template_update_product_tag_success.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            result = update_tag_for_sellable_products(params={
                'id': file_import_id
            })
            m.db.session.commit()
            db_sellable_tag = SellableProductTag.query.filter(
                SellableProductTag.sku == '124'
            ).first()
            result_import = m.FileImport.query.get(file_import_id)
            self.assertEqual(result_import.status, 'done')
            assert db_sellable_tag.tags == 'tag1', result

    def test_backgroundJob_importUpdateProductTag__found_multiple_result_for_one_seller_sku_show_error_request_input_uom(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/import_update_product_tag/template_update_product_tag_found_multiple_result_for_one_seller_sku.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_result = update_tag_for_sellable_products(params={
                'id': file_import.id
            })

        assert import_result[0] == 'Không tìm được sản phẩm với sku tương ứng, vui lòng nhập chính xác uom và uom_ratio để tìm đúng sản phẩm'


    def test_backgroundJob_importUpdateProductTag__update_fail_cannot_find_seller_sku(self):
        file_import = fake.file_import(
            user_info=self.user,
            type=self.import_type,
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/import_update_product_tag/template_update_product_tag_cannot_find_sku.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_result = update_tag_for_sellable_products(params={
                'id': file_import.id
            })

        assert import_result[0] == 'Sản phẩm không tồn tại'
