# coding=utf-8
import logging
import shutil
import base64 as b64
import os
from mock import patch


import config
from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class TestUpdateBrandImage(APITestCase):
    ISSUE_KEY = 'CATALOGUE-519'
    FOLDER = '/Brands/Update/Images'

    def url(self):
        return '/brands/images'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.brand_updated_signal.send')
        self.mock_signal = self.patcher.start()
        self.user = fake.iam_user()
        self.brand = fake.brand()
        self.fake_brand = fake.brand()
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        self.logo = b64_image

    def test_return400__MissingCode(self):
        with logged_in_user(self.user):
            data = {
                'logo': self.logo
            }
            code, _ = self.call_api(data=data)

            self.assertEqual(400, code)

    def test_return400__MissingLogo(self):
        with logged_in_user(self.user):
            data = {
                'code': 'abc'
            }
            code, _ = self.call_api(data=data)

            self.assertEqual(400, code)

    def test_return400__NotExistBrand(self):
        with logged_in_user(self.user):
            data = {
                'code': f'{self.brand.code}abcxyz'
            }
            code, _ = self.call_api(data=data)

            self.assertEqual(400, code)

    @patch('catalog.services.brand.save_logo_image')
    def test_return200__Success(self, mock):
        with logged_in_user(self.user):
            mock.return_value = fake.text()
            data = {
                'code': self.brand.code,
                'logo': self.logo
            }
            code, _ = self.call_api(data=data)

            self.assertEqual(200, code)

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
