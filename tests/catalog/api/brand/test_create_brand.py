import logging
import random
import datetime
import shutil

import os
from mock import patch
import base64 as b64

import config
from catalog import models as m
from tests.faker import fake
from tests.catalog.api import APITestCase

_author_ = 'Dung.BV'
_logger_ = logging.getLogger(__name__)


class TestCreateBrand(APITestCase):
    ISSUE_KEY = 'SC-230'

    def url(self):
        return '/brands'

    def method(self):
        return 'POST'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.brand_created_signal.send')
        self.mock_signal = self.patcher.start()
        self.active_brand = [fake.brand(name='Phong Vũ'),
                             fake.brand(name='Le le le')]
        self.inactive_brand = fake.brand(is_active=0)
        self.data = {
            'name': fake.name(),
            'code': fake.text(),
            'docRequest': random.choice([True, False])
        }
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png',
                  'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode(
            'utf-8')
        self.data['logo'] = b64_image

    def assert_create_brand_success(self, res):
        """

        :param res:
        :return:
        """
        brand_res = res['result']
        self.assertEqual(self.data['name'], brand_res['name'])
        self.assertEqual(self.data['code'], brand_res['code'])
        self.assertEqual(self.data['docRequest'], brand_res['docRequest'])
        self.mock_signal.assert_called_once()

    @patch('catalog.services.brand.send_to_image_service')
    def test_passValidData__returnCreateSuccess(self, mock):
        """

        :return:
        """
        mock.return_value = fake.text()
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        self.assert_create_brand_success(body)

    @patch('catalog.services.brand.send_to_image_service')
    def test_passNameCaseSensitive__raiseBadRequestException(self, mock):
        mock.return_value = fake.text()
        self.data['name'] = self.active_brand[1].name.lower()
        code, body = self.call_api(data=self.data)
        assert code == 400
        assert body['message'] == 'Tên thương hiệu đã tồn tại trong hệ thống'

    def test_passEmptyData__returnInvalidResponse(self):
        """

        :return:
        """
        code, body = self.call_api(data={
            "name": "",
            "code": "",
            "docRequest": ""
        })
        self.assertEqual(400, code)

    def test_missingName__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('name')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_missingCode__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('code')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    @patch('catalog.services.brand.save_logo_image')
    def test_missingLogo__returnCreateSuccess(self, mock):
        """

        :return:
        """
        mock.return_value = f'{self.data["code"][0]}/{self.data["code"]}'
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        self.assert_create_brand_success(body)

    def tearDown(self):
        shutil.rmtree(
            os.path.join(
                config.ROOT_DIR,
                'media',
                'brand'
            ),
            ignore_errors=True
        )
        self.patcher.stop()

