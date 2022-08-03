from catalog import models
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetSKUsOfTerminalGroup(APITestCase):
    ISSUE_KEY = 'CATALOGUE-51'

    def setUp(self):
        self.user = fake.iam_user()
        self.terminal_group = fake.terminal_group(seller_id=self.user.seller_id)
        self.seller_terminal_group = fake.seller_terminal_group(
            seller_id=self.user.seller_id,
            group_id=self.terminal_group.id
        )
        self.sku_terminal_group = [
            fake.sellable_product_terminal_group(terminal_group=self.terminal_group)
            for _ in range(11)
        ]

    def url(self):
        return '/sellable_products/terminal_groups/{}/products'

    def method(self):
        return 'GET'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def test_returnSuccuesfully(self):
        code, body = self.call_api(
            url=self.url().format(self.terminal_group.code)
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['skus']), 10)
        self.assertEqual(body['result']['currentPage'], 1)
        self.assertEqual(body['result']['pageSize'], 10)
        self.assertEqual(body['result']['totalRecords'], 11)

        result = body['result']['skus']
        skus = [sku.id for sku in self.sku_terminal_group]
        for i in range(10):
            self.assertIn(result[i]['id'], skus)
            self.assertEqual(self.sku_terminal_group[i].terminal_group_code, self.terminal_group.code)

    def test_returnEmptySkus(self):
        terminal_group_code = fake.terminal_group(seller_id=self.user.seller_id).code
        code, body = self.call_api(
            url=self.url().format(terminal_group_code)
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['skus']), 0)
        self.assertEqual(body['result']['currentPage'], 1)
        self.assertEqual(body['result']['pageSize'], 10)
        self.assertEqual(body['result']['totalRecords'], 0)

    def test_passNotExistTerminalGroupCode(self):
        code, body = self.call_api(
            url=self.url().format('abc')
        )

        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['skus']), 0)
        self.assertEqual(body['result']['currentPage'], 1)
        self.assertEqual(body['result']['pageSize'], 10)
        self.assertEqual(body['result']['totalRecords'], 0)

    def test_passNotAllowToSellingInTerminalGroupCode(self):
        invalid_terminal_group_code = fake.terminal_group().code
        code, body = self.call_api(
            url=self.url().format(invalid_terminal_group_code)
        )

        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['skus']), 0)
        self.assertEqual(body['result']['currentPage'], 1)
        self.assertEqual(body['result']['pageSize'], 10)
        self.assertEqual(body['result']['totalRecords'], 0)
