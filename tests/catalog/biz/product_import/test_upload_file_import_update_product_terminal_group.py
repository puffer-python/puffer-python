# coding=utf-8
import os

from sqlalchemy import and_

import config
import unittest

from mock import patch

import pytest

from catalog import models
from catalog.biz.product_import.update_terminal_groups import update_terminal_groups
from tests import logged_in_user
from tests.faker import fake
from tests.utils import JiraTest


class MockAppRequestContext:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        pass


class MockUploadResult:
    def json(self):
        return {"url": "https://test.com"}


def get_uom_code_by_name(seller_id, uom_name):
    data = models.AttributeOption.query.filter(
        models.AttributeOption.seller_id.in_([0, seller_id]),
        models.AttributeOption.value == uom_name
    ).first()
    if data:
        return data.code
    return None


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
class ImportUpdateProductTerminalGroup(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-630'
    FOLDER = '/Import/Update_product_terminal_group'

    def setUp(self):
        self.empty_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_empty_terminal_group.xlsx")
        self.spaces_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_all_spaces_terminal_group.xlsx")
        self.valid_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_valid_terminal_group.xlsx")
        self.valid_one_terminal_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_valid_one_terminal_group.xlsx")
        self.valid_only_add_terminal_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_valid_only_add_terminal_group.xlsx")
        self.valid_only_delete_terminal_template_path = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_valid_only_delete_terminal_group.xlsx")

        self.multiple_result_for_one_seller_sku = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_found_multiple_result_for_one_seller_sku.xlsx")
        self.not_found_seller_sku = os.path.join(
            config.ROOT_DIR, "tests/storage/template/import_update_product_terminal_group/template_not_found_seller_sku.xlsx")

        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.uom_attribute = self.fake_uom(self.attribute_set)

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
            attribute_set_id=self.attribute_set.id
        ) for i in range(3)]

        self.sellable_product = self.sellable_products[0]

        self.upload_result_patcher = patch('catalog.biz.product_import.ImportHandler._upload_result')
        self.mock_upload_result = self.upload_result_patcher.start()
        self.mock_upload_result.return_value = MockUploadResult()

        self.app_request_context_patcher = patch(
            'catalog.biz.product_import.update_terminal_groups.app.request_context')
        self.mock_app_request_context = self.app_request_context_patcher.start()
        self.mock_app_request_context.return_value = MockAppRequestContext(self.user)

        self.get_uom_patcher = patch('catalog.services.attributes.attribute.AttributeService.get_uom_code_by_name')
        self.mock_get_uom = self.get_uom_patcher.start()
        self.mock_get_uom.side_effect = get_uom_code_by_name

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
        fake.attribute_option(uom_attribute.id, value='CHIEC', code='CHIEC', seller_id=self.user.seller_id)
        fake.attribute_option(uom_attribute.id, value='HOP', code='HOP', seller_id=self.user.seller_id)
        fake.attribute_option(uom_attribute.id, value='LOC', code='LOC', seller_id=self.user.seller_id)
        fake.attribute_option(uom_ratio_attribute.id, value='1', code='1', seller_id=self.user.seller_id)
        fake.attribute_option(uom_ratio_attribute.id, value='2', code='2', seller_id=self.user.seller_id)
        fake.attribute_option(uom_ratio_attribute.id, value='4', code='4', seller_id=self.user.seller_id)

        return uom_attribute

    def import_file(self, template_path):
        file_import = fake.file_import(
            user_info=self.user,
            type='import_update_product_terminal_groups',
            status='new',
            path=template_path
        )
        return file_import.id

    def test_backgroundJob_successfullyWithActiveSku(self):
        terminal_group = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(group_id=terminal_group.id, seller_id=terminal_group.seller_id)
        self.sellable_product.editing_status_code = 'approved'
        models.db.session.commit()
        sellable_product_id = self.sellable_product.id
        terminal_group_code = terminal_group.code
        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            sellableProduct = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code == terminal_group_code).first()

            self.assertEqual(process.total_row_success, 1)
            self.assertIsNotNone(sellableProduct)

    def test_backgroundJob_successfullyWithInactiveSku(self):
        terminal_group = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(
            group_id=terminal_group.id, seller_id=terminal_group.seller_id)
        self.sellable_product.editing_status_code = 'inactive'
        models.db.session.commit()
        sellable_product_id = self.sellable_product.id
        terminal_group_code = terminal_group.code
        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            sellableProduct = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code == terminal_group_code).first()

            self.assertEqual(process.total_row_success, 1)
            self.assertIsNotNone(sellableProduct)

    def test_backgroundJob_successfullyWithMultipleDeletedTerminals(self):
        terminal_group1 = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group2 = fake.terminal_group(
            code='CP02', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group3 = fake.terminal_group(
            code='CP03', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group5 = fake.terminal_group(
            code='CP05', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(group_id=terminal_group1.id, seller_id=terminal_group1.seller_id)
        fake.seller_terminal_group(group_id=terminal_group2.id, seller_id=terminal_group2.seller_id)
        fake.seller_terminal_group(group_id=terminal_group5.id, seller_id=terminal_group5.seller_id)

        self.sellable_product = self.sellable_products[1]

        fake.sellable_product_terminal_group(terminal_group=terminal_group3, sellable_product=self.sellable_product)
        fake.sellable_product_terminal_group(terminal_group=terminal_group5, sellable_product=self.sellable_product)
        file_import_id = self.import_file(self.valid_template_path)
        sellable_product_id = self.sellable_product.id

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            countSellableProductApplied = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP01', 'CP02'])).count()
            countSellableProductOld = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP05'])).count()
            countSellableProductRemoved = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP03'])).count()

            self.assertEqual(process.total_row_success, 1)
            self.assertEqual(countSellableProductApplied, 2)
            self.assertEqual(countSellableProductOld, 1)
            self.assertEqual(countSellableProductRemoved, 0)

    def test_backgroundJob_successfullyWithMultipleAddedTerminals(self):
        terminal_group1 = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group2 = fake.terminal_group(
            code='CP02', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group3 = fake.terminal_group(
            code='CP03', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group4 = fake.terminal_group(
            code='CP04', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(group_id=terminal_group1.id, seller_id=terminal_group1.seller_id)
        fake.seller_terminal_group(group_id=terminal_group2.id, seller_id=terminal_group2.seller_id)

        self.sellable_product = self.sellable_products[1]

        fake.sellable_product_terminal_group(terminal_group=terminal_group3, sellable_product=self.sellable_product)
        fake.sellable_product_terminal_group(terminal_group=terminal_group4, sellable_product=self.sellable_product)
        file_import_id = self.import_file(self.valid_template_path)
        sellable_product_id = self.sellable_product.id

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            countSellableProductApplied = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP01', 'CP02'])).count()
            countSellableProductRemoved = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP03', 'CP04'])).count()

            self.assertEqual(process.total_row_success, 1)
            self.assertEqual(countSellableProductApplied, 2)
            self.assertEqual(countSellableProductRemoved, 0)

    def test_backgroundJob_successfullyWithOnlyDeleteTerminals(self):
        terminal_group3 = fake.terminal_group(
            code='CP03', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group4 = fake.terminal_group(
            code='CP04', seller_id=self.user.seller_id, is_active=True, type='SELL')
        self.sellable_product = self.sellable_products[1]

        fake.sellable_product_terminal_group(terminal_group=terminal_group3, sellable_product=self.sellable_product)
        fake.sellable_product_terminal_group(terminal_group=terminal_group4, sellable_product=self.sellable_product)
        file_import_id = self.import_file(self.valid_only_delete_terminal_template_path)
        sellable_product_id = self.sellable_product.id

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            countSellableProductApplied = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id).count()

            self.assertEqual(process.total_row_success, 1)
            self.assertEqual(countSellableProductApplied, 0)

    def test_backgroundJob_successfullyWithMultipleAddedTerminals(self):
        terminal_group1 = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group2 = fake.terminal_group(
            code='CP02', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group3 = fake.terminal_group(
            code='CP03', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group4 = fake.terminal_group(
            code='CP04', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(group_id=terminal_group1.id, seller_id=terminal_group1.seller_id)
        fake.seller_terminal_group(group_id=terminal_group2.id, seller_id=terminal_group2.seller_id)

        self.sellable_product = self.sellable_products[1]

        fake.sellable_product_terminal_group(terminal_group=terminal_group3, sellable_product=self.sellable_product)
        fake.sellable_product_terminal_group(terminal_group=terminal_group4, sellable_product=self.sellable_product)
        file_import_id = self.import_file(self.valid_template_path)
        sellable_product_id = self.sellable_product.id

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            countSellableProductApplied = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP01', 'CP02'])).count()
            countSellableProductRemoved = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP03', 'CP04'])).count()

            self.assertEqual(process.total_row_success, 1)
            self.assertEqual(countSellableProductApplied, 2)
            self.assertEqual(countSellableProductRemoved, 0)

    def test_backgroundJob_successfullyWithOnlyAddTerminals(self):
        terminal_group1 = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        terminal_group2 = fake.terminal_group(
            code='CP02', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(group_id=terminal_group1.id, seller_id=terminal_group1.seller_id)
        fake.seller_terminal_group(group_id=terminal_group2.id, seller_id=terminal_group2.seller_id)
        file_import_id = self.import_file(self.valid_only_add_terminal_template_path)
        sellable_product_id = self.sellable_product.id

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            countSellableProductAppliedByGroup = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id,
                models.SellableProductTerminalGroup.terminal_group_code.in_(['CP01', 'CP02'])).count()
            countSellableProductApplied = models.SellableProductTerminalGroup.query.filter(
                models.SellableProductTerminalGroup.sellable_product_id == sellable_product_id).count()

            self.assertEqual(process.total_row_success, 1)
            self.assertEqual(countSellableProductAppliedByGroup, 2)
            self.assertEqual(countSellableProductApplied, 2)

    def test_backgroundJob_emptyTerminalCode(self):
        file_import_id = self.import_file(self.empty_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_allSpacesTerminalCode(self):
        file_import_id = self.import_file(self.spaces_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_notExistedTerminal(self):
        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_notActiveTerminal(self):
        self.terminal_group = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=False)
        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_invalidTypeTerminal(self):
        self.terminal_group = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='ABC')
        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_sellerNotBelongToTerminal(self):
        terminal_group = fake.terminal_group(
            code='CP01', seller_id=self.user.seller_id, is_active=True, type='SELL')
        fake.seller_terminal_group(
            group_id=terminal_group.id, seller_id=terminal_group.seller_id+1000)

        file_import_id = self.import_file(self.valid_one_terminal_template_path)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_importUpdateProductStatus_foundMultipleResult(self):
        file_import_id = self.import_file(self.multiple_result_for_one_seller_sku)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)

    def test_backgroundJob_importUpdateProductStatus_cannotFindSellerSku(self):
        file_import_id = self.import_file(self.not_found_seller_sku)

        with logged_in_user(self.user):
            update_terminal_groups(params={
                'id': file_import_id
            })

            process = models.FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 0)
