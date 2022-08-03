# coding=utf-8
import os

import config
import unittest
from werkzeug.test import EnvironBuilder
from mock import patch

import pytest

from catalog import models, app, celery
from catalog.biz.product_import import import_product_task
from catalog.biz.product_import.base import Importer
from catalog.biz.product_import.create_product import CreateProductTask
from catalog.biz.product_import.create_product_basic_info import import_product_basic_info_task
from catalog.biz.product_import.create_product_quickly import CreateProductQuicklyTask, ImportProductQuickly
from catalog.biz.result_import import capture_import_result, CreateProductImportSaver, capture_import_result_task
from catalog.extensions.flask_cache import cache
from catalog.models import Product, SellableProduct, ProductVariant, FileImport \
    , SellableProductBarcode
from tests import logged_in_user
from tests.faker import fake
from tests.utils import JiraTest


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
class CreateProduct(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-1188'
    FOLDER = '/Import/Create_product'

    def setUp(self):
        self.template_dir = os.path.join(config.ROOT_DIR, 'tests', 'storage', 'template')
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=True).id)
        self.unit = fake.unit(name='Cái')
        self.brand = fake.brand(name='EPSON')
        fake.brand(name='Brand name')
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

    def tearDown(self):
        self.sellable_create_signal_patcher.stop()
        self.save_excel_patcher.stop()
        self.request_provider.stop()
        self.request_import_variant_image.stop()
        self.app_request_context_patcher.stop()
        cache.clear()

    def fake_attribute_set(self, is_variation=1, **kwargs):
        attribute_set = fake.attribute_set(**kwargs)
        attribute_group = fake.attribute_group(set_id=attribute_set.id)
        self.attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_group_attribute(attribute_id=self.attributes[0].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=self.attributes[1].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)

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

    def test_backgroundJob_createProductBasicInfo_importTypeDON_createSuccessfully(self):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_DON.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()
        sku_barcodes = SellableProductBarcode.query.filter(
            SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

        assert 2 == len(products)
        assert 2 == len(variants)
        assert 2 == len(sellable_products)

        process = FileImport.query.get(file_import_id)
        assert 2 == process.total_row_success

        result_import = models.ResultImport.query.all()
        assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
        assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
        assert len(result_import) == 2
        assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
        assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
        # CATALOGUE-1015: Check multiple barcodes
        assert len(sku_barcodes) == 2
        assert sellable_products[0].barcode == sku_barcodes[1].barcode

    def test_backgroundJob_createProductBasicInfo_importTypeCHAAndCON_createSuccessfully(self):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_CHA_CON.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()
        sku_barcodes = SellableProductBarcode.query.filter(
            SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

        self.assertEqual(len(products), 1)
        self.assertEqual(len(variants), 2)
        self.assertEqual(len(sellable_products), 2)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 2)

        result_import = models.ResultImport.query.all()
        assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
        assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
        assert len(result_import) == 2
        assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
        assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
        # CATALOGUE-1015: Check multiple barcodes
        assert len(sku_barcodes) == 2
        assert sellable_products[0].barcode == sku_barcodes[1].barcode

    def test_backgroundJob_createProduct_importTypeCHAAndCON_createSuccessfully(self):
        """
        input: CHA and 2 CON without variant names
        return: Created Successfully
        """

        attribute_set = self.fake_attribute_set()
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_successfully_CHA_CON.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()
            sku_barcodes = SellableProductBarcode.query.filter(
                SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

            assert 1 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)

            process = FileImport.query.get(file_import_id)
            assert process.total_row_success == 2

            result_import = models.ResultImport.query.all()
            assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
            assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
            assert len(result_import) == 2
            assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
            assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
            # CATALOGUE-1015: Check multiple barcodes
            assert len(sku_barcodes) == 2
            assert sellable_products[0].barcode == sku_barcodes[1].barcode
            # assert auto-generated variant name
            assert variants[0].name == 'Máy in kim EPSON LQ-310 (Trắng, S)'
            assert variants[1].name == 'Máy in kim EPSON LQ-310 (Đỏ, M)'
            assert sellable_products[0].name == 'Máy in kim EPSON LQ-310 (Trắng, S)'
            assert sellable_products[1].name == 'Máy in kim EPSON LQ-310 (Đỏ, M)'

    def test_backgroundJob_createProduct_importTypeCHAAndCON_success_with_variants_name(self):
        """
        input: CHA and 2 CON with specific variant names
        return: Created Successfully
        """

        attribute_set = self.fake_attribute_set(is_variation=False)
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(
                config.ROOT_DIR,
                "tests/storage/template/import_create_product_and_save_result/template_create_CHA_CON_success_with_variants_name.xlsx",
            ),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()

            assert 1 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)
            # assert given variant name
            assert variants[0].name == 'mytest_variant'
            assert variants[1].name == 'mytest_variant_2'
            assert sellable_products[0].name == 'mytest_variant'
            assert sellable_products[1].name == 'mytest_variant_2'

    def test_backgroundJob_createPorduct_importTypeDON_createSuccessfully(self):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_DON.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()
            sku_barcodes = SellableProductBarcode.query.filter(
                SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

            assert 2 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)

            process = FileImport.query.get(file_import_id)
            assert process.total_row_success == 2

            result_import = models.ResultImport.query.all()
            assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
            assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
            assert len(result_import) == 2
            assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
            assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
            # CATALOGUE-1015: Check multiple barcodes
            assert len(sku_barcodes) == 2
            assert sellable_products[0].barcode == sku_barcodes[1].barcode

    def test_backgroundJob_createPorduct_importTypeDON_create2Failed2(self):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_4_DON_2_Failed.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()
            sku_barcodes = SellableProductBarcode.query.filter(
                SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

            assert 2 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)

            process = FileImport.query.get(file_import_id)
            assert process.total_row_success == 2

            result_import = models.ResultImport.query.all()
            assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
            assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
            assert len(result_import) == 4
            assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
            assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
            # CATALOGUE-1015: Check multiple barcodes
            assert len(sku_barcodes) == 2
            assert sellable_products[0].barcode == sku_barcodes[1].barcode

    def test_backgroundJob_createPorduct_importTypeDON_version1_createSuccessfully(self):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_DON_with_version.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()

            assert 2 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)

    def test_backgroundJob_createProductBasicInfo_importTypeDON_version1_createSuccessfully(self):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_DON_with_version.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()

        assert 2 == len(products)
        assert 2 == len(variants)
        assert 2 == len(sellable_products)

    def test_backgroundJob_createPorduct_importTypeDON_parseDescription(self):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_DON_parseDescription.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            product = Product.query.first()
            assert product.description == 'Máy in kim <br> <br> <br> EPSON LQ-310.'
            assert product.detailed_description == 'Máy in kim <br> <br> <br> EPSON LQ-310.'

    def test_backgroundJob_createPorduct_importTypeDON_attirbuteOptions(self):
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        fake.attribute_option(
            attribute_id=self.attributes[0].id,
            seller_id=self.user.seller_id,
            value='Vàng đồng'
        )

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(
                config.ROOT_DIR,
                "tests/storage/template/import_create_product_and_save_result/template_create_DON_attribute_options.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            attribute_options = models.AttributeOption.query.all()
            assert len(attribute_options) == 7

    def test_backgroundJob_createProduct_importTypeCHAAndCON_rollbackWhenAConFailed(self):
        """
        input: CHA and 2 CON. 1 CON failed
        return: no product is created
        """

        attribute_set = self.fake_attribute_set()
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_CHA_CON_1CONFailed.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })

            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()

            assert 0 == len(products)
            assert 0 == len(variants)
            assert 0 == len(sellable_products)

            process = FileImport.query.get(file_import_id)
            assert process.total_row_success == 0

            result_import = models.ResultImport.query.all()
            assert len(result_import) == 2

    def test_backgroundJob_createProduct_importTypeCHAAndCON_duplicatedSellerSku(self):
        """
        input: CHA and 2 CON
        return: Created Successfully
        """

        attribute_set = self.fake_attribute_set()
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_successfully_CHA_CON_fail_uniqueness.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
            products = Product.query.all()
            variants = ProductVariant.query.all()
            sellable_products = SellableProduct.query.all()
            sku_barcodes = SellableProductBarcode.query.filter(
                SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

            assert 1 == len(products)
            assert 2 == len(variants)
            assert 2 == len(sellable_products)

            process = FileImport.query.get(file_import_id)
            assert process.total_row_success == 2

            result_import = models.ResultImport.query.all()
            assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
            assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
            assert len(result_import) == 5
            assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
            assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
            assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
            # CATALOGUE-1015: Check multiple barcodes
            assert len(sku_barcodes) == 2
            assert sellable_products[0].barcode == sku_barcodes[1].barcode

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_import_create_quick_create_fail_empty_uom(self, mock_object, mock_get_temrinal_groups):
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
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_failed_uom_null.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                error_msg = 'Đơn vị tính không đúng. Vui lòng nhập chính xác thông tin (xem ở Dữ liệu mẫu)'
                assert create_product_quickly_task.result[1] == error_msg
                assert create_product_quickly_task.result[2] == error_msg
                assert create_product_quickly_task.result[3] == error_msg
                assert create_product_quickly_task.result[4] == error_msg
                assert create_product_quickly_task.total_row_success == 0

                products = Product.query.all()
                variants = ProductVariant.query.all()
                sellable_products = SellableProduct.query.all()
                self.assertEqual(len(products), 0)
                self.assertEqual(len(variants), 0)
                self.assertEqual(len(sellable_products), 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_import_create_basic_create_fail_empty_uom(self, mock_object):
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set()
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_failed_CHA_CON_uom_null.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_task = CreateProductTask(
                    file_id=file_import.id,
                    cls_importer=Importer
                )
                create_product_task.run()
                unit_error_msg = 'Đơn vị tính không đúng. Vui lòng nhập chính xác thông tin (xem ở Dữ liệu mẫu)'
                child_product_error = 'Một trong các sản phẩm con bị sai'
                assert create_product_task.result[3] == unit_error_msg
                assert create_product_task.result[4] == child_product_error
                assert create_product_task.result[5] == unit_error_msg
                assert create_product_task.result[6] == unit_error_msg
                assert create_product_task.result[8] == unit_error_msg
                assert create_product_task.total_row_success == 0

                products = Product.query.all()
                variants = ProductVariant.query.all()
                sellable_products = SellableProduct.query.all()
                self.assertEqual(len(products), 0)
                self.assertEqual(len(variants), 0)
                self.assertEqual(len(sellable_products), 0)

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_import_create_quick_create_successfully_with_multiple_spaces_brand(self, mock_object,
                                                                                mock_get_temrinal_groups):
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00')
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set(is_variation=0)
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully_brand_multiple_spaces.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                assert create_product_quickly_task.total_row_success == 4

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_create_quick_create_successfully_with_empty_terminal_group(self, mock_object, mock_get_temrinal_groups):
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00')
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set(is_variation=0)
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully_empty_terminal_group.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                sku = models.SellableProduct.query.first()
                price = models.SellableProductPrice.query.filter(
                    models.SellableProductPrice.sellable_product_id == sku.id).first()
                assert price.terminal_group_ids == str(
                    [terminal_group['id'] for terminal_group in self.terminal_groups])

    @patch('catalog.biz.product_import.create_product_quickly.get_terminal_groups')
    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_create_quick_create_successfully_with_partially_correct_terminal_group(self, mock_object,
                                                                                    mock_get_temrinal_groups):
        mock_get_temrinal_groups.return_value = self.terminal_groups
        fake.tax(code='00')
        with logged_in_user(self.user):
            with app.request_context(EnvironBuilder().get_environ()):
                attribute_set = self.fake_attribute_set(is_variation=0)
                self.fake_uom(attribute_set)
                file_import = fake.file_import(
                    user_info=self.user,
                    type='create_product_quickly',
                    status='new',
                    path=os.path.join(config.ROOT_DIR,
                                      "tests/storage/template/import_create_product_and_save_result/template_create_quick_successfully_partially_correct_terminal_group.xlsx"),
                    set_id=attribute_set.id
                )
                create_product_quickly_task = CreateProductQuicklyTask(
                    file_id=file_import.id,
                    cls_importer=ImportProductQuickly
                )
                create_product_quickly_task.run()
                sku = models.SellableProduct.query.first()
                price = models.SellableProductPrice.query.filter(
                    models.SellableProductPrice.sellable_product_id == sku.id).first()
                assert price.terminal_group_ids == str(
                    [terminal_group['id'] for terminal_group in self.terminal_groups[0:2]])

    def test_backgroundJob_createProductBasicInfo_importTypeCHAAndCON_duplicatedSellerSku(self):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_CHA_CON_fail_uniqueness.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()
        sku_barcodes = SellableProductBarcode.query.filter(
            SellableProductBarcode.sellable_product_id == sellable_products[0].id).all()

        self.assertEqual(len(products), 1)
        self.assertEqual(len(variants), 2)
        self.assertEqual(len(sellable_products), 2)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 2)

        result_import = models.ResultImport.query.all()
        assert result_import[0].data.get('sku') != result_import[0].data.get('seller_sku')
        assert result_import[1].data.get('sku') != result_import[1].data.get('seller_sku')
        assert len(result_import) == 5
        assert sellable_products[0].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[1].sku in [result.data.get('sku') for result in result_import]
        assert sellable_products[0].seller_sku in [result.data.get('seller_sku') for result in result_import]
        assert sellable_products[1].seller_sku in [result.data.get('seller_sku') for result in result_import]
        # CATALOGUE-1015: Check multiple barcodes
        assert len(sku_barcodes) == 2
        assert sellable_products[0].barcode == sku_barcodes[1].barcode

    @patch('catalog.biz.listing.producer.send')
    def test_backgroundJob_createProductBasicInfo_importTypeCHAAndCON_countProductDetail(self, mock_producer):
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_CHA_CON.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })
        self.assertEqual(mock_producer.call_count, 6)

    @patch('catalog.biz.listing.producer.send')
    def test_importTypeCHAAndCON_withDescription_Cha_or_Con(self, mock_producer):
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_CHA_CON_with_description.xlsx"),
            set_id=None
        )

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })
        self.assertEqual(mock_producer.call_count, 12)
        sku = models.SellableProduct.query.filter(
            models.SellableProduct.seller_sku == 'vin-sku-456'
        ).first()
        seo_info = models.SellableProductSeoInfoTerminal.query.filter(
            models.SellableProductSeoInfoTerminal.sellable_product_id == sku.id
        ).first()
        self.assertEqual(seo_info.description, 'Mô tả ở cha')
        self.assertEqual(seo_info.short_description, 'Đặc điểm nổi bật ở cha')

        sku = models.SellableProduct.query.filter(
            models.SellableProduct.seller_sku == 'test-sku-458'
        ).first()
        seo_info = models.SellableProductSeoInfoTerminal.query.filter(
            models.SellableProductSeoInfoTerminal.sellable_product_id == sku.id
        ).first()
        self.assertEqual(seo_info.description, 'Mô tả ở con')
        self.assertEqual(seo_info.short_description, 'Đặc điểm nổi bật ở con')

    @patch('catalog.biz.listing.producer.send')
    def test_backgroundJob_createProduct_importTypeCHAAndCON_countProductDetail(self, mock_producer):
        """
        input: CHA and 2 CON
        return: Created Successfully
        """
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set()
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_successfully_CHA_CON.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
        self.assertEqual(mock_producer.call_count, 6)

    @patch('catalog.biz.listing.producer.send')
    def test_backgroundJob_createProductBasicInfo_importTypeDON_countSignals(self, mock_producer):
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_DON.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })
        self.assertEqual(mock_producer.call_count, 6)

    @patch('catalog.biz.listing.producer.send')
    def test_import_with_barcode_is_number(self, mock_producer):
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_DON_barcode_number.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })
        self.assertEqual(mock_producer.call_count, 6)

    @patch('catalog.biz.listing.producer.send')
    def test_backgroundJob_createPorduct_importTypeDON_countSignals(self, mock_producer):
        self.sellable_create_signal_patcher.stop()
        attribute_set = self.fake_attribute_set(is_variation=0)
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_DON.xlsx"),
            set_id=attribute_set.id
        )

        file_import_id = file_import.id
        with logged_in_user(self.user):
            import_product_task(params={
                'id': file_import_id,
                'environ': EnvironBuilder().get_environ(),
            })
        self.assertEqual(mock_producer.call_count, 6)

    def test_backgroundJob_createProductBasicInfo_importTypeDON_missingRequiredFields(self):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_create_product_and_save_result/template_create_product_basic_info_DON_missing_required_fields.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })
        result_import = models.ResultImport.query.all()
        assert 2 == len(result_import)
        assert 'Nhóm sản phẩm bỏ trống hoặc không chính xác.' == result_import[0].message
