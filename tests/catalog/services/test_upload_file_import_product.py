# coding=utf-8

import io
import os
import unittest

import json
from abc import ABC
from copy import deepcopy

from mock import patch

import pytest
import requests
import pandas as pd
import numpy as np
from werkzeug.datastructures import FileStorage
from werkzeug.test import EnvironBuilder

import config
from catalog import models
from catalog.biz.product_import import import_product_task
from catalog.extensions.flask_cache import cache

from catalog.models import FileImport
from catalog.services.imports import FileImportService
from catalog.extensions import exceptions as exc
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from flask import _request_ctx_stack

TITLE_ROW_OFFSET = 6
service = FileImportService.get_instance()


class UploadFileImportProductTestCase(APITestCase, ABC):
    ISSUE_KEY = 'SC-462'

    def setUp(self):
        out = io.BytesIO()
        self.total_row = fake.random_int(50)
        pd.DataFrame(data=np.random.random((TITLE_ROW_OFFSET + self.total_row, 20))).to_excel(out,
                                                                                              'Import_SanPham')
        out.seek(0)
        self.file = FileStorage(
            stream=out,
            filename=fake.text(),
            content_type='application/vnd.ms-excel'
        )

        self.attribute_set = fake.attribute_set()
        self.user = fake.iam_user()
        self.url = fake.url()

    def assertResponse(self, import_record):
        assert import_record.path == self.url
        assert import_record.attribute_set_id == self.attribute_set.id
        assert import_record.created_by == self.user.email
        assert import_record.seller_id == self.user.seller_id
        assert import_record.status == 'new'
        assert import_record.type == 'create_product'
        assert import_record.name == self.file.filename
        assert import_record.total_row == self.total_row
        assert len(import_record.key) == 10

    @patch('requests.post')
    @patch('catalog.extensions.signals.product_import_signal.send')
    def test_passValiddata__returnImportRecord(self, mock_signal, mock_request):
        resp = requests.Response()
        resp.status_code = 200
        resp._content = json.dumps({
            'url': self.url
        }).encode('utf-8')
        mock_request.return_value = resp
        mock_signal.return_value = None
        import_record = service.import_product(self.file, self.attribute_set.id, self.user)
        self.assertResponse(import_record)

    @patch('requests.post')
    @patch('catalog.extensions.signals.product_import_signal.send')
    def test_raiseException__whenCallFileServiceFail(self, mock_signal, mock_request):
        resp = requests.Response()
        resp.status_code = 400
        resp._content = json.dumps({}).encode('utf-8')
        mock_request.return_value = resp
        mock_signal.return_value = None
        with pytest.raises(exc.BadRequestException) as error_info:
            service.import_product(self.file, self.attribute_set.id, self.user)
        assert error_info.value.message == 'Upload file không thành công'


class MockAppRequestContext:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        # _request_ctx_stack.push(CeleryUser(deepcopy(self.user)))
        pass

    def __exit__(self, *args, **kwargs):
        pass


class ImportProductTaskTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-345'

    def setUp(self):
        self.template_dir = os.path.join(config.ROOT_DIR, 'tests', 'storage', 'template')
        self.user = fake.iam_user()
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
            seller_id=self.default_platform_owner.id,
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
        self.app_request_context_patcher = patch('catalog.biz.product_import.create_product.app.request_context')

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
        self.save_excel_patcher.stop()
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

    def load_results(self):
        self.products = models.Product.query.all()
        self.variants = models.ProductVariant.query.all()
        self.variant_attributes = models.VariantAttribute.query.all()
        self.sellable_products = models.SellableProduct.query.all()
        self.attributes = models.Attribute.query.all()
        self.uom_attribute_options = models.Attribute.query.filter(
            models.Attribute.code == 'uom'
        ).first().options

    @patch('catalog.biz.result_import.CreateProductImportCapture._call_job', return_value=None)
    def test_importTypeCHAAndCON__returnCreateSuccessfully(self, capture_mock):
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
            path=os.path.join(self.template_dir, 'template_create_successfully_CHA_CON.xlsx'),
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
            self.assertEqual(len(self.variants), 2)
            self.assertEqual(len(self.variant_attributes), 8)
            self.assertEqual(len(self.sellable_products), 2)
            self.assertEqual(len(self.uom_attribute_options), 3)
            process = FileImport.query.get(file_import_id)
            self.assertEqual(process.total_row_success, 2)
