# coding=utf-8
import logging
from mock import patch

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UpdateSellableProductTerminalTestCase(APITestCase):
    ISSUE_KEY = 'SC-386'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellables = [fake.sellable_product(
            variant_id=fake.product_variant().id,
            seller_id=self.seller.id
        ) for _ in range(3)]
        self.terminals = [fake.terminal(
            is_active=True,
            seller_id=self.seller.id,
            terminal_type='online'
        ) for _ in range(3)]

        self.data = {
            "skus": [sellable.sku for sellable in self.sellables],
            "sellerTerminals": [{
                "applySellerId": self.seller.id,
                "terminals": [{
                    "terminalType": "online",
                    "terminalCodes": [terminal.code for terminal in self.terminals]
                }]
            }]
        }

    def method(self):
        return 'POST'

    def url(self):
        return '/sellable_products/terminals'

    def test_passValidData__returnUpdateSuccess(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
