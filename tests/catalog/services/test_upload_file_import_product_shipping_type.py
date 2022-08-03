# coding=utf-8

import os

from abc import ABC

from mock import patch

from werkzeug.test import EnvironBuilder

import config
from catalog import models
from catalog.biz.product_import import import_product_task
from catalog.extensions.flask_cache import cache

from catalog.models import FileImport
from catalog.services.imports import FileImportService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

TITLE_ROW_OFFSET = 6
service = FileImportService.get_instance()


class MockAppRequestContext:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        pass


class CreateProductDetailInfo(APITestCase, ABC):
    ISSUE_KEY = 'CATALOGUE-635'
    FOLDER = '/Import/Create_product_detail/shipping_types'

    def setUp(self):
        self.template_dir = os.path.join(config.ROOT_DIR, 'tests', 'storage', 'template')
        self.seller = fake.seller(manual_sku=False)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.terminal_group = fake.terminal_group()
        self.unit = fake.unit(name='Cái')
        self.brand = fake.brand(name='EPSON')
        self.type = fake.misc(data_type='product_type', name='Sản phẩm')
        self.tax = fake.tax(label='Thuế 10%')
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
            seller_id=self.default_platform_owner.id
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

        self.sellable_create_signal_patcher = patch('catalog.extensions.signals.sellable_create_signal.send')
        self.save_excel_patcher = patch('catalog.biz.product_import.create_product.save_excel')
        self.request_terminal_group = patch('catalog.biz.product_import.base.get_all_terminals')
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')
        self.app_request_context_patcher = patch('catalog.biz.product_import.create_product.app.request_context')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_terminal_group = self.request_terminal_group.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()
        self.mock_app_request_context = self.app_request_context_patcher.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_terminal_group.return_value = [self.terminal_group.code]
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)
        cache.clear()

    def tearDown(self):
        self.save_excel_patcher.stop()
        self.request_terminal_group.stop()
        self.request_provider.stop()
        self.request_import_variant_image.stop()
        self.app_request_context_patcher.stop()
        cache.clear()

    def fake_attribute_set(self, is_variation=1):
        attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(
            set_id=attribute_set.id,
            system_group=False
        )
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_option(attributes[0].id, value='Vàng')
        fake.attribute_option(attributes[0].id, value='Đỏ')
        fake.attribute_option(attributes[1].id, value='S')
        fake.attribute_option(attributes[1].id, value='XXL')

        fake.attribute_group_attribute(
            attribute_id=attributes[0].id,
            group_ids=[attribute_group.id],
            is_variation=is_variation
        )
        fake.attribute_group_attribute(
            attribute_id=attributes[1].id,
            group_ids=[attribute_group.id],
            is_variation=is_variation
        )

        return attribute_set

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(
            set_id=attribute_set.id,
            system_group=True
        )
        uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=0
        )
        fake.attribute_option(uom_attribute.id, value='Cái')
        fake.attribute_option(uom_attribute.id, value='Chiếc')
        fake.attribute_option(uom_ratio_attribute.id, value='1')
        fake.attribute_option(uom_ratio_attribute.id, value='2')

        return uom_attribute

    def fake_shipping_type(self, shipping_type_name, add_category=False):
        shipping_type = fake.shipping_type(name=shipping_type_name)
        if add_category:
            fake.category_shipping_type(
                self.category.id,
                shipping_type.id
            )
        return shipping_type.id

    def __get_sku_shipping_type(self, sku_id, shipping_type_id):
        return models.SellableProductShippingType.query.filter(models.SellableProductShippingType.
                                                               sellable_product_id == sku_id,
                                                               models.SellableProductShippingType.
                                                               shipping_type_id == shipping_type_id).first()

    def load_results(self):
        self.products = models.Product.query.all()
        self.variants = models.ProductVariant.query.all()
        self.sellable_products = models.SellableProduct.query.all()
        self.sellable_product_shipping_types = models.SellableProductShippingType.query.all()

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_import_detail_product_failed_with_only_one_not_exists_shipping_type(self, capture_mock):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(self.template_dir, 'template_create_DON_shipping_type.xlsx'),
            set_id=attribute_set.id
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            self.load_results()
            self.assertEqual(len(self.products), 0)
            self.assertEqual(len(self.variants), 0)
            self.assertEqual(len(self.sellable_products), 0)
            self.assertEqual(len(self.sellable_product_shipping_types), 0)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row, 1)
            self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_import_detail_product_failed_with_multy_not_exists_shipping_type(self, capture_mock):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)
        self.fake_shipping_type('abcxyz')

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(self.template_dir, 'template_create_DON_shipping_type_multy_not_exists.xlsx'),
            set_id=attribute_set.id
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            self.load_results()
            self.assertEqual(len(self.products), 0)
            self.assertEqual(len(self.variants), 0)
            self.assertEqual(len(self.sellable_products), 0)
            self.assertEqual(len(self.sellable_product_shipping_types), 0)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row, 1)
            self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_import_detail_product_success_with_exists_shipping_type(self, capture_mock):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)
        s1_id = self.fake_shipping_type('abcxyz')
        s2_id = self.fake_shipping_type('abc')
        s3_id = self.fake_shipping_type('xyz')

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(self.template_dir, 'template_create_DON_shipping_type_multy_not_exists.xlsx'),
            set_id=attribute_set.id
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            self.load_results()
            sku_shipping_type1 = self.__get_sku_shipping_type(self.sellable_products[0].id, s1_id)
            sku_shipping_type2 = self.__get_sku_shipping_type(self.sellable_products[0].id, s2_id)
            sku_shipping_type3 = self.__get_sku_shipping_type(self.sellable_products[0].id, s3_id)
            self.assertEqual(len(self.products), 1)
            self.assertEqual(len(self.variants), 1)
            self.assertEqual(len(self.sellable_products), 1)
            self.assertEqual(len(self.sellable_product_shipping_types), 3)
            self.assertIsNotNone(sku_shipping_type1)
            self.assertIsNotNone(sku_shipping_type2)
            self.assertIsNotNone(sku_shipping_type3)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row, 1)
            self.assertEqual(process.total_row_success, 1)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_import_detail_product_success_without_shipping_type_no_shipping_type_category(self, capture_mock):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)
        self.fake_shipping_type('abcxyz')

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(self.template_dir, 'template_create_DON_no_shipping_type.xlsx'),
            set_id=attribute_set.id
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            self.load_results()
            self.assertEqual(len(self.products), 1)
            self.assertEqual(len(self.variants), 1)
            self.assertEqual(len(self.sellable_products), 1)
            self.assertEqual(len(self.sellable_product_shipping_types), 0)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row, 1)
            self.assertEqual(process.total_row_success, 1)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_import_detail_product_success_without_shipping_type_has_shipping_type_category(self, capture_mock):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)
        s1_id = self.fake_shipping_type('abcxyz', add_category=True)
        s2_id = self.fake_shipping_type('abc', add_category=True)
        s3_id = self.fake_shipping_type('xyz', add_category=True)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(self.template_dir, 'template_create_DON_no_shipping_type.xlsx'),
            set_id=attribute_set.id
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            self.load_results()
            sku_shipping_type1 = self.__get_sku_shipping_type(self.sellable_products[0].id, s1_id)
            sku_shipping_type2 = self.__get_sku_shipping_type(self.sellable_products[0].id, s2_id)
            sku_shipping_type3 = self.__get_sku_shipping_type(self.sellable_products[0].id, s3_id)
            self.assertEqual(len(self.products), 1)
            self.assertEqual(len(self.variants), 1)
            self.assertEqual(len(self.sellable_products), 1)
            self.assertEqual(len(self.sellable_product_shipping_types), 3)
            self.assertIsNotNone(sku_shipping_type1)
            self.assertIsNotNone(sku_shipping_type2)
            self.assertIsNotNone(sku_shipping_type3)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row, 1)
            self.assertEqual(process.total_row_success, 1)
