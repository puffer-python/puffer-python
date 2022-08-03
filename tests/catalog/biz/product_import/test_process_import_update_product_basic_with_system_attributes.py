# coding=utf-8
import os
from abc import ABCMeta
from unittest.mock import patch

import config
from catalog import models as m
from catalog.biz.product_import.import_update_product_basic_info import GeneralUpdateImporter
from tests import logged_in_user
from tests.catalog import ATTRIBUTE_TYPE
from tests.catalog.api import APITestCaseWithMysqlByFunc
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


class ProcessImportUpdateProductBasicWithSystemAttributesTestCase(APITestCaseWithMysqlByFunc, metaclass=ABCMeta):
    ISSUE_KEY = 'CATALOGUE-1446'
    FOLDER = '/Import/ProcessImportUpdateProductBasic/SystemAttributes'

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

        self.attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(set_id=self.attribute_set.id, system_group=True)
        self.sys_attribute_1 = fake.attribute(code='sys_attribute_1', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.TEXT)
        self.sys_attribute_2 = fake.attribute(code='sys_attribute_2', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.NUMBER)
        self.sys_attribute_3 = fake.attribute(code='sys_attribute_3', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.SELECTION)
        self.sys_attribute_4 = fake.attribute(code='sys_attribute_4', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.MULTIPLE_SELECT)
        self.sys_attribute_5 = fake.attribute(code='sys_attribute_5', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.NUMBER)
        self.sys_attribute_6 = fake.attribute(code='sys_attribute_6', group_ids=[attribute_group.id],
                                              value_type=ATTRIBUTE_TYPE.NUMBER, is_unsigned=1)

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
        unit1 = fake.attribute_option(uom_attribute.id, code='CAI1', value='Cái', seller_id=0)
        fake.attribute_option(uom_attribute.id, value='Chiếc')
        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku='sku1', seller_id=self.user.seller_id,
                                                       uom_code=unit1.code, uom_ratio=1, is_bundle=0,
                                                       variant_id=self.variant1.id)
        self.product_type = fake.misc(data_type='product_type', code='COC')
        self.shipping_type_default = fake.shipping_type(is_default=1)

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
                'update_product_basic_info',
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
            executor = GeneralUpdateImporter(file_import.id)
            executor.run()
            return executor, file_import

    def _new_option(self, attribute, value):
        return fake.attribute_option(attribute.id, value=value)

    def _get_option(self, attribute, value):
        return m.AttributeOption.query.filter(m.AttributeOption.attribute_id == attribute.id,
                                              m.AttributeOption.value == value).first()

    def _get_variant_attribute(self, attribute, value):
        return m.VariantAttribute.query.filter(m.VariantAttribute.variant_id == self.variant1.id,
                                               m.VariantAttribute.attribute_id == attribute.id,
                                               m.VariantAttribute.value == value).first()

    def assert_result(self, file_name, message, total_row_success=0):
        executor, file_import = self._execute(file_name)

        self.assertEqual(executor.result['Message'][0], message)
        self.assertEqual(total_row_success, file_import.total_row_success)
        return executor

    def test_import_success_with_existed_and_new_attribute_options(self):
        option3 = self._new_option(self.sys_attribute_3, 'value3')

        self.assert_result('success_with_system_attributes.xlsx', None, 1)

        # New options created when import
        option41 = self._get_option(self.sys_attribute_4, 'value41')
        option42 = self._get_option(self.sys_attribute_4, 'value42')

        # Variant attributes
        variant_attribute1 = self._get_variant_attribute(self.sys_attribute_1, 'value1')
        variant_attribute2 = self._get_variant_attribute(self.sys_attribute_2, '2')
        variant_attribute3 = self._get_variant_attribute(self.sys_attribute_3, f'{option3.id}')
        variant_attribute4 = self._get_variant_attribute(self.sys_attribute_4, f'{option41.id},{option42.id}')

        self.assertIsNotNone(option41)
        self.assertIsNotNone(option42)
        self.assertIsNotNone(variant_attribute1)
        self.assertIsNotNone(variant_attribute2)
        self.assertIsNotNone(variant_attribute3)
        self.assertIsNotNone(variant_attribute4)

    def test_import_failed_with_not_number_value(self):
        self.assert_result('failed_with_system_attributes_not_number.xlsx', f'Giá trị thuộc tính {self.sys_attribute_5.name} phải là số', 0)

    def test_import_failed_with_not_positive_value(self):
        self.assert_result('failed_with_system_attributes_not_positive_number.xlsx', f'Giá trị thuộc tính {self.sys_attribute_6.name} phải lớn lớn hơn 0', 0)