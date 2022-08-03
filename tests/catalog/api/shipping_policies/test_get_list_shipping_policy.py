# coding=utf-8
import logging

__author__ = 'Kien.HT'

import random

from tests.catalog.api import APITestCase
from tests.faker import fake

_logger = logging.getLogger(__name__)


class ShippingPolicyListTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-58'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(20)]
        self.providers = [fake.seller_prov() for _ in range(10)]

        self.policies = [fake.shipping_policy(
            category_ids=[category.id for category in
                          random.sample(self.categories, random.randint(0, len(self.categories)))],
            provider_ids=[provider.id for provider in
                          random.sample(self.providers, random.randint(0, len(self.providers)))]
        )]
        self.page = 1
        self.page_size = 10

    def method(self):
        return 'GET'

    def url(self):
        return '/shipping_policies'

    def query_with(self, params):
        query_params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        if 'page' not in params:
            query_params = f'{query_params}&page={self.page}'
        if 'pageSize' not in params:
            query_params = f'{query_params}&pageSize={self.page_size}'
        url = f'{self.url()}?{query_params}'

        code, body = self.call_api(url=url, method=self.method())

        return code, body['result']

    def test_passExactPolicyName__returnExactPolicy(self):
        policy = self.policies[0]
        code, body = self.query_with({
            'name': policy.name
        })

        self.assertEqual(200, code)
        self.assertEqual(policy.id,body['policies'][0]['id'])

    def test_passRandomPolicyName__returnListPolicy(self):
        query = 'a'
        total = len([policy for policy in self.policies if query in policy.name])

        code, body = self.query_with({
            'name': query
        })

        self.assertEqual(200, code)
        self.assertEqual(total, body['totalRecords'])

    def test_passPolicyNameTooLong__raiseValidationError(self):
        code, _ = self.query_with({
            'name': fake.text(length=256)
        })

        self.assertEqual(400, code)

    def test_passIsActiveStatus__returnListPolicies(self):
        total = len([policy for policy in self.policies if policy.is_active])

        code, body = self.query_with({
            'isActive': 1
        })

        self.assertEqual(200, code)
        self.assertEqual(total, body['totalRecords'])

    def test_passInvalidIsActive__raiseValidationError(self):
        code, _ = self.query_with({
            'isActive': 69
        })

        self.assertEqual(400, code)

    def test_passShippingType__returnListPolicies(self):
        shipping_type = 'all'
        total = len([policy for policy in self.policies
                     if policy.shipping_type == shipping_type])

        code, body = self.query_with({
            'shippingType': shipping_type
        })

        self.assertEqual(200, code)
        self.assertEqual(total, body['totalRecords'])

    def test_invalidShippingType__raiseValidationError(self):
        code, _ = self.query_with({
            'shippingType': 'ahihi'
        })

        self.assertEqual(400, code)

    def test_passProviderIds__returnListPolicies(self):
        providers = random.sample(self.providers, 3)
        code, body = self.query_with({
            'providerIds': ','.join([str(provider.id) for provider in providers])
        })

        self.assertEqual(200, code)

    def test_passInvalidProviderId__returnEmptyList(self):
        code, body = self.query_with({
            'providerIds': 'abc'
        })

        self.assertEqual(200, code)
        self.assertEqual(0, len(body['policies']))

    def test_passCategoryIds__returnListPolicies(self):
        categories = random.sample(self.categories, 3)
        code, body = self.query_with({
            'categoryIds': ','.join([str(category.id) for category in categories])
        })

        self.assertEqual(200, code)

    def test_passInvalidCategoryId__returnEmptyList(self):
        code, body = self.query_with({
            'categoryIds': 'abc'
        })

        self.assertEqual(200, code)
        self.assertEqual(0, len(body['policies']))

    def test_passMultipleFilters__returnListPolicies(self):
        categories = random.sample(self.categories, 3)
        providers = random.sample(self.providers, 2)
        code, body = self.query_with({
            'categoryIds': ','.join(
                [str(category.id) for category in categories]),
            'providerIds': ','.join(
                [str(provider.id) for provider in providers])
        })

        self.assertEqual(200, code)
