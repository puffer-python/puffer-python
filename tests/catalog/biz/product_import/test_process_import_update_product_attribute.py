# coding=utf-8
import os
from abc import ABCMeta
from unittest.mock import patch

from sqlalchemy import and_

import config
from catalog.biz.product_import.import_update_images_skus import ImportUpdateImagesSkus
from catalog.biz.product_import.import_update_product_attribute import UpdateProductAttributeImporter
from catalog.biz.product_import.import_update_product_basic_info import GeneralUpdateImporter
from catalog.models import VariantAttribute, Attribute
from tests import logged_in_user
from tests.catalog import ATTRIBUTE_TYPE
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


class ProcessImportUpdateProductAttributeTestCase(APITestCaseWithMysql, metaclass=ABCMeta):
    # ISSUE_KEY = 'CATALOGUE-645'
    ISSUE_KEY = 'CATALOGUE-1295'
    FOLDER = '/Import/ProcessImportUpdateProductAttribute'

    def setUp(self):
        self.sellable_update_signal_patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.upload_file_xlsx_patcher = patch(
            'catalog.biz.product_import.import_update_product_basic_info.requests.post',
            return_value=MockResponse(
                status_code=200,
                url='url_xlsx_test',
            ))

        self.sellable_update_signal_patcher.start()
        self.upload_file_xlsx_patcher.start()

        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)

        self.category = fake.category(code='01-N001-01', seller_id=self.user.seller_id, is_active=1)
        self.brand = fake.brand(name='HITACHI', is_active=1)
        self.tax = fake.tax(label='10%')

        self.attribute_3 = fake.attribute(code='attribute_3', value_type=ATTRIBUTE_TYPE.TEXT)
        self.attribute_4 = fake.attribute(code='attribute_4', value_type=ATTRIBUTE_TYPE.TEXT)

        self.attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(set_id=self.attribute_set.id)
        fake.attribute(code='attribute_5', group_ids=[attribute_group.id], is_variation=True)

        self.attribute_6 = fake.attribute(code='attribute_6', value_type=ATTRIBUTE_TYPE.SELECTION)
        self.a6_o1 = fake.attribute_option(attribute_id=self.attribute_6.id, value='option_1')
        self.a6_o2 = fake.attribute_option(attribute_id=self.attribute_6.id, value='option_2')

        self.attribute_7 = fake.attribute(code='attribute_7', value_type=ATTRIBUTE_TYPE.MULTIPLE_SELECT)
        self.a7_o1 = fake.attribute_option(attribute_id=self.attribute_7.id, value='option_1')
        self.a7_o2 = fake.attribute_option(attribute_id=self.attribute_7.id, value='option_2')

        self.attribute_8 = fake.attribute(code='attribute_8', value_type=ATTRIBUTE_TYPE.NUMBER)

        self.attribute_set_2 = fake.attribute_set()
        uom_attribute_group = fake.attribute_group(set_id=self.attribute_set_2.id)
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
        fake.attribute_option(uom_attribute.id, value='Chiếc')

    def tearDown(self):
        self.sellable_update_signal_patcher.stop()
        self.upload_file_xlsx_patcher.stop()

    def _execute(self, file_name):
        with logged_in_user(self.user):
            file_stream = os.path.join(
                config.ROOT_DIR,
                'tests',
                'catalog',
                'api',
                'imports',
                'test_case_samples',
                'update_product_attribute',
                file_name
            )
            file_import = fake.file_import(
                user_info=self.user,
                type='import_update',
                status='new',
                path=file_stream,
                set_id=None,
                total_row_success=0
            )
            executor = UpdateProductAttributeImporter(file_import.id)
            executor.run()
            return executor, file_import

    def assert_process_fail(self, file_name, message):
        executor, file_import = self._execute(file_name)
        self.assertEqual('error', file_import.status)
        self.assertEqual(message, file_import.note)

    def assert_result(self, file_name, message, total_row_success=0):
        executor, file_import = self._execute(file_name)

        self.assertEqual(executor.result['Message'][0], message)
        self.assertEqual(total_row_success, file_import.total_row_success)
        return executor
    
    def __get_uom_attr(self):
        uom_attr = Attribute.query.filter(Attribute.code == 'uom').first()
        if not uom_attr:
            uom_attr = fake.attribute(code='uom', value_type='selection', is_variation=True)
        return uom_attr

    def test_process_fail_attribute_code_incorrect(self):
        self.assert_process_fail('incorrect_attribute_code.xlsx',
                                 'Không tồn tại các thuộc tính có mã: attribute_1,attribute_2')

    def test_process_not_found_sku(self):
        self.assert_result('not_found_sku_data.xlsx', 'Không tìm thấy sản phẩm (kiểm tra lại mã seller sku, '
                                                      'đơn vị tính và tỷ lệ quy đổi)')

    def test_process_more_than_one_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=2,
                                                       variant_id=self.variant1.id)
        self.assert_result('multi_sku_data.xlsx', 'Tìm thấy nhiều hơn 1 sản phẩm có cùng mã seller sku. '
                                                  'Vui lòng nhập thêm đơn vị tính và tỷ lệ quy đổi')

    def test_process_attribute_is_variation(self):
        self.variant0 = fake.product_variant(attribute_set_id=self.attribute_set.id)
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.assert_result('attribute_is_variation.xlsx', 'Không được sửa thuộc tính biến thể attribute_5')

    def test_process_create_new_attribute_option_in_selection_attribute(self):
        self.variant0 = fake.product_variant(attribute_set_id=self.attribute_set.id)
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.assert_result('invalid_attribute_option_in_selection_attribute.xlsx', None, 1)

    def test_process_create_new_attribute_option_in_multi_selection_attribute(self):
        self.variant0 = fake.product_variant(attribute_set_id=self.attribute_set.id)
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.assert_result('invalid_attribute_option_in_multi_selection_attribute.xlsx', None, 1)

    def test_process_valid_seller_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.assert_result('valid_data_seller_sku.xlsx', None, 1)

    def test_process_valid_seller_sku_and_uom(self):
        uom_attr = self.__get_uom_attr()
        uom_attr_option = fake.attribute_option(attribute_id=uom_attr.id, value='Bộ', seller_id=self.user.seller_id)
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_code=uom_attr_option.code, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.assert_result('valid_data_seller_sku_and_uom.xlsx', None, 1)

    def test_process_valid_seller_sku_and_uom_and_ratio(self):
        uom_attr = self.__get_uom_attr()
        uom_attr_option = fake.attribute_option(attribute_id=uom_attr.id, value='Bộ', seller_id=self.user.seller_id)
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_code=uom_attr_option.code, is_bundle=0, uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.assert_result('valid_data_seller_sku_and_uom_and_ratio.xlsx', None, 1)

    def test_process_valid_data_match_attribute(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant1.id)

        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_3.id, value='yyyy1')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_4.id, value='zzzz3')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_7.id, value=f'{self.a7_o2.id}')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_6.id, value=f'{self.a6_o2.id}')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_8.id, value='5')

        self.assert_result('valid_data.xlsx', None, 2)

        self.assert_variant_attribute(self.variant0.id, self.attribute_3.id, 'xxxx1')
        self.assert_variant_attribute(self.variant0.id, self.attribute_4.id, 'xxxx2')
        self.assert_variant_attribute(self.variant0.id, self.attribute_7.id, f'{self.a7_o1.id},{self.a7_o2.id}')
        self.assert_variant_attribute(self.variant0.id, self.attribute_6.id, f'{self.a6_o2.id}')
        self.assert_variant_attribute(self.variant0.id, self.attribute_8.id, '10')

        self.assert_variant_attribute(self.variant1.id, self.attribute_3.id, 'xxxx3')
        self.assert_variant_attribute(self.variant1.id, self.attribute_4.id, 'zzzz3')
        self.assert_variant_attribute(self.variant1.id, self.attribute_7.id, f'{self.a7_o1.id}')
        self.assert_variant_attribute(self.variant1.id, self.attribute_6.id, f'{self.a6_o1.id}')
        self.assert_variant_attribute(self.variant1.id, self.attribute_8.id, '20')

    def test_process_validDataAttributeOptions_withMultipleSpaces(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, is_bundle=0,
                                                       variant_id=self.variant1.id)

        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_3.id, value='yyyy1')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_4.id, value='zzzz3')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_7.id, value=f'Vàng Đồng')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_6.id, value=f'Vàng Đồng')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_8.id, value='5')

        self.assert_result('valid_data_attribute_options.xlsx', None, 2)

    def test_process_validData_with_uom_case_insensitive_multiple_spaces(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=1, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id,
                                                       uom_ratio=2, uom_code='CAI1', is_bundle=0,
                                                       variant_id=self.variant1.id)

        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_3.id, value='yyyy1')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_4.id, value='zzzz3')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_7.id, value=f'Vàng Đồng')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_6.id, value=f'Vàng Đồng')
        fake.variant_attribute(variant_id=self.variant1.id, attribute_id=self.attribute_8.id, value='5')

        self.assert_result('valid_data_attribute_options_uom_special_case.xlsx', None, 2)

    def assert_variant_attribute(self, variant_id, attribute_id, value):
        items = VariantAttribute.query.filter(and_(
            VariantAttribute.variant_id == variant_id,
            VariantAttribute.attribute_id == attribute_id
        )).all()
        self.assertEqual(1, len(items))
        self.assertEqual(value, items[0].value)
