# coding=utf-8

from mock import patch

from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog.api.product.variant import schema


class GetListVariantsTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1238'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.variants = [fake.product_variant(product_id=self.product.id, created_by=self.user.email)
                         for _ in range(5)]

    def assertVariantList(self, variants, data):
        for item in data:
            item.pop('images', None)
        assert len(data) == len(variants)
        real_data = schema.GenericVariant(many=True).dump(variants)
        sorted_real_data = sorted(real_data, key=lambda item: item['id'])
        sorted_data = sorted(data, key=lambda item: item['id'])
        for a, b in zip(sorted_real_data, sorted_data):
            for k, v in b.items():
                if hasattr(a, k):
                    assert v == a[v]

    def method(self):
        return 'GET'

    def url(self):
        return '/variants'

    def test_validProductId_return200(self):
        for i in range(len(self.variants)):
            variant = self.variants[i]
            fake.sellable_product(variant_id=variant.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url() + f'?productId={self.product.id}')
            assert 200 == code
            assert 'SUCCESS' == body['code']
            self.assertVariantList(self.variants, body['result']['variants'])

    def test_getPublishedVariatnOwnedByOtherUser__return200(self):
        other_user = fake.iam_user(seller_id=self.seller.id)
        self.variants.append(fake.product_variant(
            product_id=self.product.id, created_by=other_user.email,
            editing_status_code='approved'
        ))
        for i in range(len(self.variants)):
            variant = self.variants[i]
            fake.sellable_product(variant_id=variant.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url() + f'?productId={self.product.id}')
            assert 200 == code
            assert 'SUCCESS' == body['code']
            self.assertVariantList(self.variants, body['result']['variants'])

    def test_passProductIdWith5Variants_oneVariantMissingSku_return4Variants(self):
        for i in range(len(self.variants)-1):
            variant = self.variants[i]
            fake.sellable_product(variant_id=variant.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url() + f'?productId={self.product.id}')
            assert 200 == code
            assert 'SUCCESS' == body['code']
            self.assertEqual(body['result']['totalRecords'], 4)
