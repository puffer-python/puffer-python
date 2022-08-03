# coding=utf-8

import json
import logging
from mock import patch

import config
from catalog.services.categories import CategoryService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'quang.da'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class CreateCategoryTreeTestCase(APITestCase):
    ISSUE_KEY = 'SC-410'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.unit = fake.unit()
        with open(
                '{}/tests/datafiles/category.json'.format(config.ROOT_DIR),
                'r'
        ) as datafile:
            categories = json.load(datafile)
            self.categories = [fake.category_json(**data) for data in categories]
        self.payload_body = {
            "code": "DAQ",
            "name": "DAAQ",
            "parent_id": self.categories[0].id,
            "manage_serial": True,
            "auto_generate_serial": fake.boolean(),
            "attribute_set_id": self.attribute_set.id,
            "unit_id": self.unit.id,
            "tax_in_code": "DA",
            "tax_out_code": "AQ"
        }

    def assertBody(self, payload_body, obj):
        for key, value in payload_body.items():
            assert getattr(obj, key) == value

    def test_create_category_successfully(self):
        with patch('catalog.extensions.signals.ram_category_created_signal.send') as mock_signal:
            mock_signal.return_value = None
            with logged_in_user(self.user):
                category, _ = service.create_category(dict(self.payload_body))
                self.assertBody(self.payload_body, category)
                assert category.seller_id == self.user.seller_id
                assert category.path == f'1/{category.id}'
                assert category.is_active is True
