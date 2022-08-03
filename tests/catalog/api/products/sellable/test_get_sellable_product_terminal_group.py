from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetSellableProductTerminalGroup(APITestCase):
    ISSUE_KEY = 'CATALOGUE-579'
    FOLDER = '/SellableProducts/GetListByTerminalGroup'

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)
        self.sku_terminal_group = [
            fake.sellable_product_terminal_group(
                sellable_product=self.sellable_product
            ),
            fake.sellable_product_terminal_group(
                sellable_product=self.sellable_product
            )
        ]

    def url(self):
        return '/sellable_products/{}/terminal_groups'

    def method(self):
        return 'GET'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def test_returnSuccuesfully(self):
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id)
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['terminalGroups']), 2)

        result = body['result']['terminalGroups']
        self.assertIn(self.sku_terminal_group[0].terminal_group_code, result)
        self.assertIn(self.sku_terminal_group[1].terminal_group_code, result)

    def test_returnEmptyTerminalGroup(self):
        sellable_product = fake.sellable_product(seller_id=self.user.seller_id)
        code, body = self.call_api(
            url=self.url().format(sellable_product.id)
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['terminalGroups']), 0)

    def test_passInvalidSellableProductID(self):
        code, body = self.call_api(
            url=self.url().format('abc')
        )
        self.assertEqual(code, 404)
