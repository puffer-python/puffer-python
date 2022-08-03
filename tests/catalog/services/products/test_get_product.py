#coding=utf-8

import pytest

from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products import ProductService

service = ProductService.get_instance()


class GetGenericProductTestCase(APITestCase):
    # ISSUE_KEY = 'SC-388'
    ISSUE_KEY = 'SC-550'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)

    def test_passProductOwnedByUser__returnProduct(self):
        ret = service.get_product(self.product.id)
        assert ret == self.product

    def test_passApprovedProductOwnedByOtherUser__returnProduct(self):
        product = fake.product(created_by=fake.iam_user().email, editing_status_code='approved')
        ret = service.get_product(product.id)
        assert product == ret
