# coding=utf-8
import logging

__author__ = 'Kien.HT'

import random

from tests.catalog.api import APITestCase
from tests.faker import fake

_logger = logging.getLogger(__name__)


class CreateShippingPolicyTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-56'

    def method(self):
        return 'POST'

    def url(self):
        return '/shipping_policies'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]

        self.data = {
            'name': fake.text(length=200),
            'isActive': True,
            'shippingType': random.choice(['all', 'bulky', 'near']),
            'providerIds': [provider.id for provider in self.providers],
            'categoryIds': [category.id for category in self.categories]
        }

    def test_passValidData__createPolicySuccess(self):
        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)

    def test_emptyPayload__raiseBadRequestException(self):
        code, body = self.call_api()
        self.assertEqual(400, code)
