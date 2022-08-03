# coding=utf-8
import logging
import random
import shutil
from datetime import datetime
import base64 as b64
import os
from mock import patch


import config
from catalog import utils
from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class TestUpdateBrand(APITestCase):
    ISSUE_KEY = 'SC-263'

    def url(self):
        return '/brands/{brand_id}'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.brand_updated_signal.send')
        self.mock_signal = self.patcher.start()
        self.user = fake.iam_user()
        self.brand = fake.brand()
        self.fake_brand = fake.brand()
        self.inactive_brand = fake.brand(is_active=False)
        self.data = {
            'name': fake.name(),
            'docRequest': random.choice((True, False)),
            'isActive': True
        }
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png',
                  'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode(
            'utf-8')
        self.data['logo'] = b64_image

    def assert_update_success(self, res):
        for prop, val in self.brand.__dict__.items():
            if not prop.startswith('_'):
                if prop == 'path' and res[prop] is not None:
                    assert val in res[prop]
                elif prop in ['created_at', 'updated_at']:
                    self.assertEqual(
                        datetime.strftime(val, "%Y-%m-%d %H:%M:%S"),
                        res[utils.camel_case(prop)]
                    )
                else:
                    self.assertEqual(val, res[utils.camel_case(prop)])

    @patch('catalog.services.brand.save_logo_image')
    def test_passValidData__returnUpdateSuccess(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(200, code)
            self.assert_update_success(body['result'])
            self.mock_signal.assert_called_once()

    @patch('catalog.services.brand.save_logo_image')
    def test_changeNothing__returnUpdateSuccess(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            self.data.update(
                name=self.brand.name,
                docRequest=bool(self.brand.doc_request),
                isActive=bool(self.brand.is_active)
            )
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(200, code)
            self.assert_update_success(body['result'])
            self.mock_signal.assert_not_called()


    @patch('catalog.services.brand.save_logo_image')
    def test_inActiveBrand__returnBrandDeactivated(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            self.data['isActive'] = False
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(200, code)
            self.assert_update_success(body['result'])
            self.assertEqual(False, self.brand.is_active)
            self.mock_signal.assert_called_once()


    def test_deleteBrandLogo__returnBrandWithLogoNull(self):
        with logged_in_user(self.user):
            self.data['logo'] = None
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(200, code)
            self.assert_update_success(body['result'])
            self.assertEqual(None, self.brand.path)
            self.mock_signal.assert_called_once()


    @patch('catalog.services.brand.save_logo_image')
    def test_passIsActiveNone__updateSuccess(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            self.data.pop('isActive')
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(code, 200)
            self.assertEqual(body['code'], 'SUCCESS')
            self.mock_signal.assert_called_once()


    @patch('catalog.services.brand.save_logo_image')
    def test_isActiveFalse__updateSuccess(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            self.data['isActive'] = False
            url = self.url().format(brand_id=self.brand.id)
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(code, 200)
            self.assertEqual(body['code'], 'SUCCESS')
            self.mock_signal.assert_called_once()


    def test_logoNone__updateSuccess(self):
        with logged_in_user(self.user):
            url = self.url().format(brand_id=self.brand.id)
            self.data.pop('logo')
            code, body = self.call_api(self.data, url=url)

            self.assertEqual(code, 200)
            self.assertEqual(body['code'], 'SUCCESS')
            self.mock_signal.assert_called_once()

    def test_nameAndIsActiveNone__updateSuccess(self):
        fake.brand(name='123none11')
        with logged_in_user(self.user):
            url = self.url().format(brand_id=self.brand.id)
            data = {
                'logo': None
            }

            code, body = self.call_api(data, url=url)

            self.assertEqual(code, 200)
            self.assertEqual(body['code'], 'SUCCESS')
            self.mock_signal.assert_called_once()

    def tearDown(self):
        shutil.rmtree(
            os.path.join(
                config.ROOT_DIR,
                'media',
                'brand'
            ),
            ignore_errors=True
        )
