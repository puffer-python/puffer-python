#coding=utf-8

import random
from unittest import TestCase
from mock import patch

from tests.catalog.api import APITestCase
from tests.utils import JiraTest
from tests import logged_in_user
from tests.faker import fake
from catalog import utils
from catalog.services.categories.category import CategoryService
from catalog import models


service = CategoryService.get_instance()

class SyncCategoryToSrm(APITestCase, JiraTest):
    ISSUE_KEY = 'SC-654'

    def setUp(self):
        self.user = fake.iam_user()
        self.parent = fake.category()
        self.tax = fake.tax()
        self.data = {
            'name': fake.name(),
            'code': fake.text(),
            'is_active': fake.boolean(),
            'parent_id': self.parent.id,
            'tax_in_code': self.tax.code,
            'tax_out_code': self.tax.code,
        }

    def test_syncCategory__whenCreateCategory(self):
        with logged_in_user(self.user):
            with patch('catalog.biz.category.publish_category.delay') as mock_task:
                mock_task.return_value = None
                with patch('catalog.extensions.signals.ram_category_created_signal.send') as mock_create_signal:
                    service.create_category(self.data)
                    mock_create_signal.assert_called()

    def test_syncCategory__whenUpdateCategory(self):
        self.cate = fake.category()
        with logged_in_user(self.user):
            with patch('catalog.biz.category.publish_category.delay') as mock_task:
                mock_task.return_value = None
                with patch('catalog.extensions.signals.ram_category_updated_signal.send') as mock_update_signal:
                    service.update_category(data=self.data, obj_id=self.cate.id)
                    mock_update_signal.assert_called()
