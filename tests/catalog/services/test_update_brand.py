#coding=utf-8

import random
from mock import patch
import pytest

from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user

from catalog.extensions import exceptions as exc
from catalog import models as m
from catalog.services import brand


class TestServiceUpdateBrand(APITestCase):
    ISSUE_KEY = 'SC-263'

    def setUp(self):
        self.user = fake.iam_user()
        self.brand = fake.brand(is_active=True)
        self.fake_brand = fake.brand(is_active=True)
        self.inactive_brand = fake.brand(is_active=False)
        self.data = {
            'name': fake.name(),
            'logo': fake.text(),
            'doc_request': random.choice((True, False)),
            'is_active': True
        }

    def assert_log(self, brand):
        log = m.ActionLog.query.filter(
            m.ActionLog.object_id == brand.id
        ).first()
        # self.assertEqual(log is not None, True)
        # self.assertEqual(log.object_id, brand.id)

    def assert_brand_content(self, brand, data):
        for key, value in data.items():
            if hasattr(brand, key):
                if isinstance(value, bool):
                    self.assertEqual(getattr(brand, key), int(value))
                else:
                    self.assertEqual(getattr(brand, key), value)

    @patch('catalog.services.brand.save_logo_image')
    def test_with_valid_data(self, mock_save_logo):
        with logged_in_user(self.user):
            mock_save_logo.return_value = self.brand.path
            brand.update_brand(self.brand.id, self.data)
            self.assert_brand_content(self.brand, self.data)
            self.assertEqual(self.brand.path, mock_save_logo.return_value)
            self.assert_log(self.brand)

    def test_with_logo_is_none(self):
        with logged_in_user(self.user):
            self.data['logo'] = None
            brand.update_brand(self.brand.id, self.data)
            self.assert_brand_content(self.brand, self.data)
            self.assert_log(self.brand)

    def test_with_logo_not_existed(self):
        with logged_in_user(self.user):
            self.data.pop('logo')
            brand.update_brand(self.brand.id, self.data)
            self.assert_brand_content(self.brand, self.data)
            self.assert_log(self.brand)
