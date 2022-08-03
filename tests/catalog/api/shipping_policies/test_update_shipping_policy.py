# coding=utf-8
import logging

__author__ = 'Kien.HT'

import random

from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user

_logger = logging.getLogger(__name__)


class UpdateShippingPolicyTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-59'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]

        self.policy = fake.shipping_policy(
            category_ids=[category.id for category in self.categories],
            provider_ids=[provider.id for provider in self.providers]
        )

    def method(self):
        return 'PATCH'

    def url(self):
        return f'/shipping_policies/{self.policy.id}'

    def test_passValidData__updatePolicySuccess(self):
        with logged_in_user(fake.iam_user()):
            data = {
                'name': fake.text(length=200),
                'isActive': True,
                'shippingType': random.choice(['all', 'bulky', 'near']),
                'providerIds': [provider.id for provider in self.providers],
                'categoryIds': [category.id for category in self.categories]
            }
            code, body = self.call_api(data=data)
            self.assertEqual(200, code)

    def test_updateShippingPolicyNotExisted__raiseBadRequestException(self):
        url = f'/shipping_policies/12154'
        data = {
            'name': fake.text(length=200),
            'isActive': True,
            'shippingType': random.choice(['all', 'bulky', 'near']),
            'providerIds': [provider.id for provider in self.providers],
            'categoryIds': [category.id for category in self.categories]
        }

        code, _ = self.call_api(url=url, data=data)
        self.assertEqual(400, code)
