# coding=utf-8
import os

from pika.compat import long

import config
import unittest
import logging
from mock import patch

import pytest

from catalog import models
from catalog.biz.product_import.create_product_basic_info import import_product_basic_info_task
from catalog.extensions.celery import CeleryUser
from catalog.extensions.flask_cache import cache
from catalog.models import Product, SellableProduct, ProductVariant, FileImport \
    , SellableProductTerminalGroup, SellableProductShippingType
from tests import logged_in_user
from tests.faker import fake
from tests.utils import JiraTest
from flask import _request_ctx_stack

_logger = logging.getLogger(__name__)


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
class CreateProductBasicInfo(unittest.TestCase, JiraTest):
    # ISSUE_KEY = 'CATALOGUE-330'
    ISSUE_KEY = 'CATALOGUE-1295'
    FOLDER = '/Import/Create_product_basic_info'

    def setUp(self):
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)
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
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')
        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.create_product_basic_info.app.request_context')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()
        self.mock_app_request_context = self.app_request_context_patcher.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)
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
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_group_attribute(attribute_id=attributes[0].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=attributes[1].id, group_ids=[attribute_group.id],
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

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeDON_createSuccessfully(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/template_create_product_basic_info_DON.xlsx"),
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

        assert 2 == len(products)
        assert 2 == len(variants)
        assert 2 == len(sellable_products)

        process = FileImport.query.get(file_import_id)
        assert 2 == process.total_row_success

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeCHAAndCON_withMultipleUOM_createSuccessfully(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_CHA_CON.xlsx"),
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
        
        self.assertEqual(len(products), 1)
        self.assertEqual(len(variants), 2)
        self.assertEqual(len(sellable_products), 2)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 2)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_background_job_import_type_CHA_and_CON_with_multiple_UOM_create_successfully_with_uom_brand_multiple_spaces_uom_case_insensitive(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_CHA_CON_brand_uom_special_case.xlsx"),
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

        self.assertEqual(len(products), 1)
        self.assertEqual(len(variants), 2)
        self.assertEqual(len(sellable_products), 2)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 2)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_notInputtedRequiredFieldsAndInputtedInvalidValue(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)
        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_DON_with_no_and_invalid_fields.xlsx"),
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

        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)

        process = FileImport.query.get(file_import_id)
        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_notExistAttributeSet(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/template_create_product_basic_info_DON.xlsx")
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()

        self.assertEqual(len(products), 1)
        self.assertEqual(len(variants), 1)
        self.assertEqual(len(sellable_products), 1)

        process = FileImport.query.get(file_import_id)
        self.assertEqual(process.total_row_success, 1)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importProductNotUOMVariantOnly_createFail(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=1, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=1, name='Máy bơm')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=1, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_not_uom_attribute.xlsx")
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        products = Product.query.all()
        variants = ProductVariant.query.all()
        sellable_products = SellableProduct.query.all()

        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)

        process = FileImport.query.get(file_import_id)
        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeChaAndCon_ChaCreatedFail(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=1, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_CHA_CON.xlsx"),
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
        
        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)
        
        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeChaAndCon_NoConCreated(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_CHA_CON_with_no_CON_created.xlsx"),
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
        
        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)
        
        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeChaAndCon_noConInputted(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_CHA_CON_with_no_CON.xlsx"),
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
        
        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)
        
        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_duplicatedConProductAndSKU(self, mock_object):
        """
        Input: CHA and duplicated CON
        Result: no product is create successfully
        """
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_duplicated.xlsx"),
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
        
        self.assertEqual(len(products), 0)
        self.assertEqual(len(variants), 0)
        self.assertEqual(len(sellable_products), 0)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 0)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importBrandNameUpperCaseAndLowerCase_createSuccessfully(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_DON_case_insensitive.xlsx"),
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

        assert 2 == len(products)
        assert 2 == len(variants)
        assert 2 == len(sellable_products)

        process = FileImport.query.get(file_import_id)
        assert 2 == process.total_row_success

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_duplicatedSellerSku(self, mock_object):
        """
        Input: CHA and duplicated CON
        Result: no product is create successfully
        """
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_create_product_basic_info_fail_uniqueness.xlsx"),
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

        self.assertEqual(len(products), 2)
        self.assertEqual(len(variants), 4)
        self.assertEqual(len(sellable_products), 4)

        process = FileImport.query.get(file_import_id)

        self.assertEqual(process.total_row_success, 4)


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
class TestImportProductSellerSku(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-541'
    FOLDER = '/Import/Create_product_seller_sku'

    def setUp(self):
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)
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
        self.category = fake.category(
            code='05-N005-03',
            is_active=True,
            unit_id=self.unit.id,
            seller_id=self.user.seller_id,
            attribute_set_id=1
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
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')
        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.create_product_basic_info.app.request_context')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()
        self.mock_app_request_context = self.app_request_context_patcher.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)
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
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_group_attribute(attribute_id=attributes[0].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=attributes[1].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)

        return attribute_set

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id)
        uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=0
        )
        fake.attribute_option(uom_attribute.id, value='Cái')
        fake.attribute_option(uom_attribute.id, value='Chiếc')


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
class CreateProductBasicInfoWithShippingTypeDefault(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-704'
    FOLDER = '/Import/CreateProductBasicInfoWithShippingTypeDefault'

    def setUp(self):
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)
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
        fake.attribute_option(self.uom_attribute.id, value='Cái')
        fake.attribute_option(self.uom_attribute.id, value='Chiếc')

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
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')
        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.create_product_basic_info.app.request_context')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()
        self.mock_app_request_context = self.app_request_context_patcher.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)
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
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_group_attribute(attribute_id=attributes[0].id, group_ids=[attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=attributes[1].id, group_ids=[attribute_group.id],
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

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_backgroundJob_importTypeDON_createWithoutShippingType(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=0, name='Máy bơm')
        self.fake_uom(attribute_set)

        self.shipping_type_default = fake.shipping_type(is_default=1)
        shipping_type_default_id = self.shipping_type_default.id

        file_import = fake.file_import(
            user_info=self.user,
            type='create_product_basic_info',
            status='new',
            path=os.path.join(config.ROOT_DIR, "tests/storage/template/template_create_product_basic_info_DON.xlsx"),
            set_id=None
        )
        with logged_in_user(self.user):
            import_product_basic_info_task(params={
                'id': file_import.id
            })

        sellable_products = SellableProduct.query.all()

        assert 2 == len(sellable_products)

        for sellable_product in sellable_products:
            sellable_shipping_types = models.SellableProductShippingType.query.filter(
                models.SellableProductShippingType.sellable_product_id == sellable_product.id
            ).all()
            self.assertEqual(len(sellable_shipping_types), 1)
            sellable_shipping_type = sellable_shipping_types[0]
            self.assertEqual(sellable_shipping_type.shipping_type_id, shipping_type_default_id)



