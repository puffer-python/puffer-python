# coding=utf-8
import os
from abc import ABCMeta, ABC
from unittest.mock import patch

import config
from catalog import models
from catalog.biz.product_import.import_update_product_basic_info import GeneralUpdateImporter
from tests import logged_in_user
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake


class MockResponse:
    def __init__(self, status_code, headers=None, content=None, image_url=None, url=None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.image_url = image_url
        self.url = url

    def json(self):
        return {
            'image_url': self.image_url,
            'url': self.url
        }


class SetupTestCase(APITestCaseWithMysql, metaclass=ABCMeta):
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

        fake.attribute_group_attribute(attribute_id=self.attributes[0].id, group_ids=[attribute_group.id], is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=self.attributes[1].id, group_ids=[attribute_group.id], is_variation=is_variation)

        return attribute_set

    def setUp(self):
        self.sellable_common_update_signal_patcher = patch(
            'catalog.extensions.signals.sellable_common_update_signal.send')
        self.sellable_update_signal_patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.upload_file_xlsx_patcher = patch(
            'catalog.biz.product_import.import_update_product_basic_info.requests.post',
            return_value=MockResponse(
                status_code=200,
                url='url_xlsx_test',
            ))

        self.sellable_common_update_signal_patcher.start()
        self.sellable_update_signal_patcher.start()
        self.upload_file_xlsx_patcher.start()

        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)

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
        self.category = fake.category(code='01-N001-01', seller_id=self.default_platform_owner.id, is_active=1)
        self.category2 = fake.category(code='testing', seller_id=self.default_platform_owner.id, is_active=1)
        fake.category(name='Laptop not Acer', code='seller_category', seller_id=self.user.seller_id, is_active=1)
        self.brand = fake.brand(name='HITACHI', is_active=1)
        self.brand = fake.brand(name='Brand name', is_active=1)
        self.tax = fake.tax(label='10%')

        self.attribute_set = fake.attribute_set()
        uom_attribute_group = fake.attribute_group(set_id=self.attribute_set.id)
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
            is_variation=1
        )
        fake.attribute_option(uom_attribute.id, code='CAI1', value='Cái', seller_id=0)
        fake.attribute_option(uom_attribute.id, code='CHIEC1', value='Chiếc')

    def tearDown(self):
        self.sellable_common_update_signal_patcher.stop()
        self.sellable_update_signal_patcher.stop()
        self.upload_file_xlsx_patcher.stop()

    def assert_result(self, file_name, message, total_row_success=0):
        with logged_in_user(self.user):
            file_stream = os.path.join(
                config.ROOT_DIR,
                'tests',
                'catalog',
                'api',
                'imports',
                'test_case_samples',
                'update_product_basic_info',
                file_name
            )
            file_import = fake.file_import(
                user_info=self.user,
                type='update_product',
                status='new',
                path=file_stream,
                set_id=None,
                total_row_success=0
            )
            executor = GeneralUpdateImporter(file_import.id)
            executor.run()
            self.assertEqual(executor.result['Message'][0], message)
            self.assertEqual(total_row_success, file_import.total_row_success)


class ProcessImportUpdateProductBasicInfoTestCase(SetupTestCase, metaclass=ABCMeta):
    # ISSUE_KEY = 'CATALOGUE-623'
    ISSUE_KEY = 'CATALOGUE-1295'
    FOLDER = '/Import/ProcessImportUpdateProductBasicInfo'

    def test_process_not_found_sku(self):
        self.assert_result('not_found_sku_data.xlsx', 'Không tìm thấy sản phẩm '
                                                      '(kiểm tra lại mã seller sku, đơn vị tính và tỷ lệ quy đổi)')

    def test_process_more_than_one_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=2,
                                                       variant_id=self.variant1.id)
        self.assert_result('multi_sku_data.xlsx', 'Tìm thấy nhiều hơn 1 sản phẩm có cùng mã seller sku. '
                                                  'Vui lòng nhập thêm đơn vị tính và tỷ lệ quy đổi')

    def test_process_valid_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant0.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, is_bundle=0,
                                                       variant_id=self.variant1.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.product_type = fake.misc(data_type='product_type', code='COC')
        fake.shipping_type(name='shipping_type1')
        fake.shipping_type(name='shipping_type2')

        self.assert_result('valid_data.xlsx', None, 1)

    def test_process_valid_sku_with_uom_case_insensitive_and_multiple_spaces(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku4", seller_id=self.user.seller_id,
                                                       uom_ratio=1, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant0.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku5", seller_id=self.user.seller_id,
                                                       uom_ratio=2, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant1.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.variant2 = fake.product_variant()
        self.sellable_product2 = fake.sellable_product(seller_sku="sku6", seller_id=self.user.seller_id,
                                                       uom_ratio=3, uom_code='CHIEC1', is_bundle=0,
                                                       variant_id=self.variant2.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.product_type = fake.misc(data_type='product_type', code='COC1')

        self.assert_result('valid_data_uom_special_case.xlsx', None, 1)

    def test_process_valid_sku_with_multiple_spaces_brand_name(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku7", seller_id=self.user.seller_id,
                                                       uom_ratio=1, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant0.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku8", seller_id=self.user.seller_id,
                                                       uom_ratio=2, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant1.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.variant2 = fake.product_variant()
        self.sellable_product2 = fake.sellable_product(seller_sku="sku9", seller_id=self.user.seller_id,
                                                       uom_ratio=3, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant2.id,
                                                       attribute_set_id=self.attribute_set.id)

        self.product_type = fake.misc(data_type='product_type', code='COC2')

        self.assert_result('valid_data_brand_special_case.xlsx', None, 3)


class ProcessImportUpdateProductBasicInfoWithDefaultShippingTypeTestCase(SetupTestCase,
                                                                         ABC):
    ISSUE_KEY = 'CATALOGUE-706'
    FOLDER = '/Import/ProcessImportUpdateProductBasicInfoWithDefaultShippingType'

    def test_process_valid_sku_without_shipping_type(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, is_bundle=0,
                                                       variant_id=self.variant1.id)

        self.product_type = fake.misc(data_type='product_type', code='COC')
        self.shipping_type_default = fake.shipping_type(is_default=1)

        self.assert_result('valid_data_without_shipping_type.xlsx', None, 1)

        sellable_shipping_types = models.SellableProductShippingType.query.filter(
            models.SellableProductShippingType.sellable_product_id == self.sellable_product0.id
        ).all()
        self.assertEqual(len(sellable_shipping_types), 1)
        sellable_shipping_type = sellable_shipping_types[0]
        self.assertEqual(sellable_shipping_type.shipping_type_id, self.shipping_type_default.id)


class ProcessImportUpdateProductBasicInfoWithShippingTypeTestCase(
    SetupTestCase,
    ABC
):
    ISSUE_KEY = 'CATALOGUE-1372'
    FOLDER = '/Import/ProcessImportUpdateProductBasicInfoWithShippingTypeTestCase'

    def test_process_should_return_error_not_found_shipping_type(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, is_bundle=0,
                                                       variant_id=self.variant1.id)

        self.product_type = fake.misc(data_type='product_type', code='COC')
        fake.shipping_type(name='shipping_type1')

        self.assert_result('shipping_type_not_found.xlsx', 'Loại hình vận chuyển "shipping_type2" không tồn tại hoặc đã bị vô hiệu.', 0)

    def test_process_should_return_error_inactive_shipping_type(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, is_bundle=0,
                                                       variant_id=self.variant1.id)

        self.product_type = fake.misc(data_type='product_type', code='COC')
        fake.shipping_type(name='shipping_type inactive', is_active=False)

        self.assert_result('shipping_type_inactive.xlsx', 'Loại hình vận chuyển "shipping_type inactive" không tồn tại hoặc đã bị vô hiệu.', 0)


class ProcessImportUpdateProductBasicInfoWithDefaultCategoryTestCase(SetupTestCase, ABC):
    ISSUE_KEY = 'CATALOGUE-1297'
    FOLDER = '/Import/UploadFileImportUpdateProductBasicInfo'

    def assert_result(self, file_name, message, total_row_success=0):
        with logged_in_user(self.user):
            file_stream = os.path.join(
                config.ROOT_DIR,
                'tests',
                'catalog',
                'api',
                'imports',
                'test_case_samples',
                'update_product_basic_info',
                file_name
            )
            file_import = fake.file_import(
                user_info=self.user,
                type='update_product',
                status='new',
                path=file_stream,
                set_id=None,
                total_row_success=0
            )
            executor = GeneralUpdateImporter(file_import.id)
            executor.run()
            self.assertEqual(executor.result['Message'][0], message)
            self.assertEqual(total_row_success, file_import.total_row_success)

    def test_process_1_valid_sku_1_failed_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku2", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant1.id)

        self.product_type = fake.misc(data_type='product_type', code='COC')
        fake.product_category(category_id=self.category2.id, product_id=self.sellable_product1.product_id)
        self.assert_result('invalid_category_data.xlsx', 'Giá trị seller_category=>Laptop not Acer không tồn tại cho category', 1)
        product_category = models.ProductCategory.query.filter(
            models.ProductCategory.product_id == self.sellable_product1.product_id,
            models.Category.id == models.ProductCategory.category_id,
            models.Category.seller_id == self.default_platform_owner.id
        ).first()
        assert product_category.category_id == self.category.id
