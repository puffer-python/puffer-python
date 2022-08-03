# coding=utf-8
import logging

from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class GetShippingPolicyTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-57'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]
        self.policy = fake.shipping_policy(
            category_ids=[category.id for category in self.categories],
            provider_ids=[provider.id for provider in self.providers]
        )

    def method(self):
        return 'GET'

    def url(self):
        return f'/shipping_policies/{self.policy.id}'

    def test_getExistedPolicy__returnSuccess(self):
        code, body = self.call_api()

        self.assertEqual(200, code)

    def test_policyNotExisted__returnNotFoundException(self):
        code, _ = self.call_api(url='/shipping_policies/645654623')

        self.assertEqual(404, code)
