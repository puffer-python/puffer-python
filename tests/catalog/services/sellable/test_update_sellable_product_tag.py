#coding=utf-8

from catalog import models
from catalog.services.products.sellable import update_sellable_product_tag
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class SellableProductTagTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-312'

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)
        self.sellable_product_tag = fake.sellable_product_tag(
            sellable_product_id=self.sellable_product.id,
            sku=self.sellable_product.sku,
            created_by=self.user.email,
            updated_by=self.user.email,
        )

        self.data = {
            'sellable_product_id': self.sellable_product.id,
            'sku': self.sellable_product.sku,
            'tags': 'ABC',
            'overwrite': 'Y'
        }

    def test_updateSellableProductTag(self):
        user = fake.iam_user(seller_id=self.user.seller_id)
        with logged_in_user(user):
            update_sellable_product_tag(**self.data)

            result = models.SellableProductTag.query.get(self.sellable_product_tag.id)
            self.assertEqual(result.updated_by, user.email)
            self.assertEqual(result.created_by, self.user.email)
            self.assertEqual(result.tags, 'ABC')


