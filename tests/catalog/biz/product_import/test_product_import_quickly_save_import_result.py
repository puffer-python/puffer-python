# coding=utf-8
import os
import config
import pytest
import random
import datetime
import unittest

from mock import patch
from tests import logged_in_user
from catalog import models
from tests.faker import fake
from tests.utils import JiraTest
from catalog.biz.result_import import CreateProductImportCapture, CreateProductImportSaver, ImportStatus
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
class TestProductImportQuicklySaveImportResult(unittest.TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-1415'
    FOLDER = '/Import/Histories/Background_SaveResult'

    def setUp(self):
        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)
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
        self.request_terminal_group = patch('catalog.biz.product_import.base.get_all_terminals')
        self.request_provider = patch('catalog.validators.sellable.provider_srv.get_provider_by_id')
        self.request_import_variant_image = patch('catalog.biz.product_import.base.Importer.create_variant_images')

        self.mock_sellable_create_signal = self.sellable_create_signal_patcher.start()
        self.mock_save_excel = self.save_excel_patcher.start()
        self.mock_terminal_group = self.request_terminal_group.start()
        self.mock_provider = self.request_provider.start()
        self.mock_import_variant_image = self.request_import_variant_image.start()

        self.mock_save_excel.return_value = 'done'
        self.mock_terminal_group.return_value = [self.terminal_group.code]
        self.mock_provider.return_value = self.provider
        self.mock_import_variant_image.return_value = True
        cache.clear()

    def tearDown(self):
        self.sellable_create_signal_patcher.stop()
        self.save_excel_patcher.stop()
        self.request_terminal_group.stop()
        self.request_provider.stop()
        self.request_import_variant_image.stop()
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

    def assert_row_data(self, expected, actual):
        """
        Comparing the data of expected and actual
        :param dict expected:
        :param dict actual:
        :return:
        """

        for key in expected:
            assert expected[key] == actual.get(key)

    def run_capture_result(self, capture_object):
        """

        :param CreateProductImportCapture capture_object:
        :return:
        """
        saver = CreateProductImportSaver(
            import_id=capture_object.import_id,
            status=capture_object.status or random.choice(
                [ImportStatus.FAILURE, ImportStatus.SUCCESS, ImportStatus.FATAL]),
            message=capture_object.message or "",
            data=capture_object.data or {},
            product_id=capture_object.product_id or None,
            output=capture_object.output or "",
            tag=capture_object.tag or "")
        saver.save()

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

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_check_updated_at(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_product_quickly/create_product_quickly_SUCCESS.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                        importer=fake.result_import_row(type='DON'))
            self.run_capture_result(import_capture)

        result_import = models.ResultImport.query.filter().first()
        assert result_import.id
        assert result_import.updated_at.date() == datetime.datetime.now().date()

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_check_updated_by(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_import_product_quickly_CHA_CON_with_no_CON_created.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                        importer=fake.result_import_row(type='DON'))
            self.run_capture_result(import_capture)

        result_import = models.ResultImport.query.filter().first()
        assert result_import.id
        assert result_import.updated_by == self.user.email

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_with_fail_row_error_data_status_failure(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_product_quickly.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                        importer=fake.result_import_row(type='DON'))
            import_capture.status = 'failure'
            self.run_capture_result(import_capture)

        result_import = models.ResultImport.query.filter().first()
        assert result_import.id
        assert result_import.status == ImportStatus.FAILURE
        assert result_import.data == import_capture.data

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_with_fail_row_exception_status_fatal(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_product_quickly.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                        importer=fake.result_import_row(type='DON'))
            import_capture.status = 'fatal'
            self.run_capture_result(import_capture)

        result_import = models.ResultImport.query.filter().first()
        assert result_import.id
        assert result_import.status == ImportStatus.FATAL
        assert result_import.data == import_capture.data

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_successful_with_data(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/import_product_quickly.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id

        with logged_in_user(self.user):
            import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                        importer=fake.result_import_row(type='DON'))
            self.run_capture_result(import_capture)

        result_import = models.ResultImport.query.filter().first()
        assert result_import.id
        assert result_import.updated_by == self.user.email
        self.assert_row_data(result_import.data, import_capture.data)

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_save_result_with_success_and_failed_rows(self, mock_object):
        attribute_set = self.fake_attribute_set(is_variation=0, name='Sữa')
        self.fake_uom(attribute_set)

        file_import = fake.file_import(
            user_info=self.user,
            type='import_product_quickly',
            status='new',
            path=os.path.join(config.ROOT_DIR,
                              "tests/storage/template/template_import_quickly.xlsx"),
            set_id=None
        )
        file_import_id = file_import.id
        rows = []
        with logged_in_user(self.user):
            for i in range(random.randint(2, 10)):
                import_capture = CreateProductImportCapture(attribute_set_id=attribute_set.id, import_id=file_import_id,
                                                            importer=fake.result_import_row(type='DON'))
                import_capture.status = random.choice([ImportStatus.SUCCESS, ImportStatus.FAILURE])
                self.run_capture_result(import_capture)
                rows.append(import_capture)

        result_imports = models.ResultImport.query.filter().all()
        assert len(result_imports) == len(rows)
        success_rows = list(filter(lambda x: x.status == ImportStatus.SUCCESS, rows))
        success_records = list(filter(lambda x: x.status == ImportStatus.SUCCESS, rows))
        assert len(success_rows) == len(success_records)
        failure_rows = list(filter(lambda x: x.status == ImportStatus.SUCCESS, rows))
        failure_records = list(filter(lambda x: x.status == ImportStatus.SUCCESS, rows))
        assert len(failure_rows) == len(failure_records)
