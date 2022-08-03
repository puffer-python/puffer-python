import os
import json
import random

import config
import pytest
import unittest

from mock import patch
from tests import logged_in_user
from catalog import models, app
from tests.faker import fake
from tests.utils import JiraTest
from werkzeug.test import EnvironBuilder
from catalog.constants import RAM_QUEUE
from catalog.biz.listing import update_product_detail
from catalog.biz.result_import import capture_import_result_task
from catalog.biz.product_import.create_product_quickly import CreateProductQuicklyTask, ImportProductQuickly
from catalog.extensions.flask_cache import cache


class MockAppRequestContext:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        # _request_ctx_stack.push(CeleryUser(deepcopy(self.user)))
        pass

    def __exit__(self, *args, **kwargs):
        pass


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
class SetupTestCase(unittest.TestCase, JiraTest):
    def setUp(self) -> None:
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=True).id)
        self.unit = fake.unit(name='Cái')
        self.type = fake.misc(data_type='product_type', name='Sản phẩm')
        self.brand = fake.brand(name='EPSON')
        self.seller_terminals = [
            fake.seller_terminal(
                seller_id=self.user.seller_id,
                terminal_id=fake.terminal(
                    terminal_type='showroom', seller_id=self.user.seller_id,
                    is_active=True, terminal_code='CP09').id),
            fake.seller_terminal(
                seller_id=self.user.seller_id,
                terminal_id=fake.terminal(terminal_type='showroom', seller_id=self.user.seller_id,
                                          terminal_code='CP04', is_active=True).id),
            fake.seller_terminal(
                seller_id=self.user.seller_id,
                terminal_id=fake.terminal(terminal_type='showroom', seller_id=self.user.seller_id, is_active=True).id)
        ]
        self.uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            is_variation=1
        )
        self.uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            is_variation=1
        )
        fake.attribute_option(self.uom_attribute.id, value='Cái', seller_id=1)
        fake.attribute_option(self.uom_attribute.id, value='Cái 1', seller_id=1)
        fake.attribute_option(self.uom_attribute.id, value='Chiếc', seller_id=1)
        self.default_platform_owner = fake.seller()
        platform_id = fake.integer()
        fake.platform_sellers(
            platform_id=platform_id,
            seller_id=self.user.seller_id,
            is_default=True
        )
        fake.platform_sellers(
            platform_id=platform_id,
            seller_id=self.default_platform_owner.id,
            is_owner=True
        )

        self.category = fake.category(
            code='05-N005-03',
            is_active=True,
            unit_id=self.unit.id,
            seller_id=self.default_platform_owner.id,
            attribute_set_id=1
        )

        fake.category(
            code='seller_category',
            is_active=True,
            unit_id=self.unit.id,
            seller_id=self.user.seller_id,
            attribute_set_id=1
        )

        fake.platform_sellers(
            seller_id=self.user.seller_id,
            platform_id=fake.integer(),
            is_default=True,
            is_owner=True
        )

        self.provider = {
            "id": 1,
            "displayName": "Hello",
            "isOwner": 0,
            "code": "Str",
            "logo": None,
            "createdAt": "2020-07-29 06:56:13",
            "slogan": "This is a string",
            "isActive": 1,
            "sellerID": self.user.seller_id,
            "name": "String",
            "updatedAt": "2020-07-29 06:56:13"
        }

        self.terminal_groups = []
        for id in range(1, 5):
            self.terminal_groups.append({
                "sellerID": fake.integer(),
                "description": "",
                "id": id,
                "isOwner": fake.boolean(),
                "code": "T" + str(id),
                "type": "SELL",
                "sellerName": "",
                "isActive": 1,
                "name": fake.text(),
            })

        self.sellable_create_signal_patcher = patch('catalog.extensions.signals.sellable_create_signal.send')
        self.save_excel_patcher = patch('catalog.biz.product_import.create_product.save_excel')
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')
        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.create_product_basic_info.app.request_context')
        self.capture_import_result_patcher = patch('catalog.biz.result_import.capture_import_result.delay')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()
        self.mock_app_request_context = self.app_request_context_patcher.start()
        self.mock_capture_import_result = self.capture_import_result_patcher.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)
        self.mock_capture_import_result.side_effect = capture_import_result_task
        cache.clear()

    def tearDown(self) -> None:
        self.sellable_create_signal_patcher.stop()
        self.save_excel_patcher.stop()
        self.request_provider.stop()
        self.request_import_variant_image.stop()
        self.app_request_context_patcher.stop()
        cache.clear()

    def fake_attribute_set(self, is_variation=1, **kwargs):
        attribute_set = fake.attribute_set(**kwargs)
        fake.attribute_group(set_id=attribute_set.id)

        return attribute_set

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id)
        fake.attribute_group_attribute(
            attribute_id=self.uom_attribute.id,
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        fake.attribute_group_attribute(
            attribute_id=self.uom_ratio_attribute.id,
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )


class ImportCreateQuicklyTestCase(SetupTestCase):
    ISSUE_KEY = 'CATALOGUE-1417'
    FOLDER = '/Import/Create_product_quickly'

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_importCreateQuickly_Successfully_send_listed_price_to_ppm(self, mock_object, mock_get_temrinal_groups):
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00')
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set()
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                assert create_product_quickly_task.result[1] == 'Thành công'
                assert create_product_quickly_task.total_row_success == 1

                products = models.Product.query.all()
                variants = models.ProductVariant.query.all()
                sellable_products = models.SellableProduct.query.all()
                self.assertEqual(len(products), 1)
                self.assertEqual(len(variants), 1)
                self.assertEqual(len(sellable_products), 1)

                update_product_detail(sellable_products[0], ppm_listed_price=True)
                ram_event = models.RamEvent.query.filter(
                    models.RamEvent.key == RAM_QUEUE.RAM_UPDATE_PRODUCT_DETAIL).first()
                self.assertTrue(ram_event)

                data = json.loads(ram_event.payload)
                self.assertTrue(data.get('ppm_listed_price'))

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_importCreateQuickly_Successfully_send_tax_out_code_to_ppm(self, mock_object, mock_get_temrinal_groups):
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00', label='Thuế 10%')
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set()
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully_tax_out_info.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                assert create_product_quickly_task.result[1] == 'Thành công'
                assert create_product_quickly_task.total_row_success == 1

                products = models.Product.query.all()
                variants = models.ProductVariant.query.all()
                sellable_products = models.SellableProduct.query.all()
                sellable_product_price = models.SellableProductPrice.query.first()
                self.assertEqual(len(products), 1)
                self.assertEqual(len(variants), 1)
                self.assertEqual(len(sellable_products), 1)
                self.assertEqual(sellable_product_price.tax_out_code, '00', sellable_product_price)

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_importCreateQuickly_Successfully_send_tax_out_code_empty_check_attribute_set(self, mock_object,
                                                                                          mock_get_temrinal_groups):
        """
        Check tax out by category
        """
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00')

        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set()
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully_tax_out_empty.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                assert create_product_quickly_task.result[1] == 'Thành công'
                assert create_product_quickly_task.total_row_success == 1

                products = models.Product.query.all()
                variants = models.ProductVariant.query.all()
                sellable_products = models.SellableProduct.query.all()
                sellable_product_price = models.SellableProductPrice.query.first()
                category = models.Category.query.first()
                sku = random.choice(sellable_products)
                self.assertEqual(sku.attribute_set_id, category.attribute_set_id)
                self.assertEqual(len(products), 1)
                self.assertEqual(len(variants), 1)
                self.assertEqual(len(sellable_products), 1)
                self.assertEqual(sellable_product_price.tax_out_code, category.tax_out_code, sellable_product_price)
