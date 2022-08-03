from copy import deepcopy

from mock import patch

from catalog import models
from catalog.models import db
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class UpsertSellableProductTerminalGroup(APITestCase):
    ISSUE_KEY = 'CATALOGUE-51'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.mock_signal = self.patcher.start()

        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellable_products = [
            fake.sellable_product(seller_id=self.seller.id, editing_status_code='approved')
            for _ in range(2)
        ]
        self.terminal_groups = [
            fake.terminal_group(seller_id=self.seller.id)
            for _ in range(2)
        ]
        self.seller_terminal_group = [
            fake.seller_terminal_group(group_id=self.terminal_groups[i].id, seller_id=self.seller.id)
            for i in range(2)
        ]
        self.sellable_product_terminal_group = fake.sellable_product_terminal_group(
            terminal_group=self.terminal_groups[0],
            sellable_product=self.sellable_products[0],
            user=self.user
        )
        self.data = {
            "sellableProducts": [sellable_product.id for sellable_product in self.sellable_products],
            "terminalGroups": [terminal_group.code for terminal_group in self.terminal_groups]
        }

    def url(self):
        return '/sellable_products/terminal_groups'

    def method(self):
        return 'POST'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def test_upsertSellableProductTerminalGroupSuccessfully(self):
        sellable_product = fake.sellable_product(seller_id=fake.seller().id)
        fake.sellable_product_terminal_group(
            terminal_group=self.terminal_groups[0],
            sellable_product=sellable_product
        )

        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )

        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['sellableProducts']), 2)
        self.assertEqual(len(body['result']['terminalGroups']), 2)

        result = models.SellableProductTerminalGroup.query.all()
        self.assertEqual(len(result), 5)

        result = models.SellableProductTerminalGroup.query.filter(
            models.SellableProductTerminalGroup.sellable_product_id.in_(self.data['sellableProducts']),
        ).all()

        self.assertEqual(len(result), 4)
        for r in result:
            self.assertIn(r.terminal_group_code, self.data['terminalGroups'])
            self.assertEqual(r.created_by, self.user.email)
            self.assertEqual(r.updated_by, self.user.email)

        self.mock_signal.assert_called()

    def test_passInvalidSKU__returnBadRequest(self):
        self.data['sellableProducts'].append(''.join(['a' for _ in range(300)]))
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)

    def test_passInvalidTerminalGroupCode__returnBadRequest(self):
        self.data['terminalGroups'].append(''.join(['a' for _ in range(300)]))
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)

    def test_passEmptySKUArray__returnBadRequest(self):
        self.data['sellableProducts'] = []
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)

    def test_passEmptyTerminalGroup__returnBadRequest(self):
        self.data['terminalGroups'] = []
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 200)

    def test_passNotExistTerminalGroupCode__returnBadRequest(self):
        data = deepcopy(self.data)
        data['terminalGroups'].append('abc')
        db.session.commit()

        code, body = self.call_api(
            url=self.url(),
            data=data
        )
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Nhóm điểm bán không tồn tại, đã bị vô hiệu hoặc có loại khác SELL')

        inactive_terminal_group_code = fake.terminal_group(
            seller_id=self.seller.id,
            is_active=False
        ).code
        data = deepcopy(self.data)
        data['terminalGroups'].append(inactive_terminal_group_code)
        code, body = self.call_api(
            url=self.url(),
            data=data
        )
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Nhóm điểm bán không tồn tại, đã bị vô hiệu hoặc có loại khác SELL')

    def test_passInvalidSKUOfSellerID__returnBadRequest(self):
        invalid_sellable = fake.sellable_product(seller_id=10).id
        self.data['sellableProducts'].append(invalid_sellable)
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không hợp lệ hoặc đã bị vô hiệu')

    def test_passValidTerminalGroupWhichSellerIsAllowedToSellingOn__returnSuccessfully(self):
        seller = fake.seller()
        valid_terminal_group = fake.terminal_group(seller_id=seller.id)
        fake.seller_terminal_group(group_id=valid_terminal_group.id, seller_id=self.seller.id)

        fake.sellable_product_terminal_group(
            terminal_group=fake.terminal_group(seller_id=seller.id),
            sellable_product=self.sellable_products[0],
            user=self.user
        )

        self.data['terminalGroups'].append(valid_terminal_group.code)

        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['sellableProducts']), 2)
        self.assertEqual(len(body['result']['terminalGroups']), 3)

        result = models.SellableProductTerminalGroup.query.all()
        self.assertEqual(len(result), 6)

        result = models.SellableProductTerminalGroup.query.filter(
            models.SellableProductTerminalGroup.sellable_product_id.in_(self.data['sellableProducts'])
        ).all()
        self.assertEqual(len(result), 6)

        for r in result:
            self.assertIn(r.terminal_group_code, self.data['terminalGroups'])
            self.assertEqual(r.created_by, self.user.email)
            self.assertEqual(r.updated_by, self.user.email)

        self.mock_signal.assert_called()

    def test_passInvalidTerminalGroupOfSellerID__returnBadRequest(self):
        invalid_terminal_group_code = fake.terminal_group().code
        self.data['terminalGroups'].append(invalid_terminal_group_code)
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Tồn tại nhóm điểm bán mà seller không được phép bán')

    def test_passInvalidTerminalGroupTypePRICE__returnBadRequest(self):
        price_terminal_group_code = fake.terminal_group(type='PRICE', seller_id=self.user.seller_id).code
        self.data['terminalGroups'].append(price_terminal_group_code)
        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Nhóm điểm bán không tồn tại, đã bị vô hiệu hoặc có loại khác SELL')


class UpsertSellableProductTerminalGroupInactiveSku(APITestCase):
    ISSUE_KEY = 'CATALOGUE-407'
    FOLDER = '/SellableProductTerminalGroup/Upsert/InactiveSku'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.sellable_update_signal.send')
        self.mock_signal = self.patcher.start()

        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellable_products = [
            fake.sellable_product(seller_id=self.seller.id, editing_status_code='inactive')
            for _ in range(2)
        ]
        self.terminal_groups = [
            fake.terminal_group(seller_id=self.seller.id)
            for _ in range(2)
        ]
        self.seller_terminal_group = [
            fake.seller_terminal_group(group_id=self.terminal_groups[i].id, seller_id=self.seller.id)
            for i in range(2)
        ]
        self.sellable_product_terminal_group = fake.sellable_product_terminal_group(
            terminal_group=self.terminal_groups[0],
            sellable_product=self.sellable_products[0],
            user=self.user
        )
        self.data = {
            "sellableProducts": [sellable_product.id for sellable_product in self.sellable_products],
            "terminalGroups": [terminal_group.code for terminal_group in self.terminal_groups]
        }

    def url(self):
        return '/sellable_products/terminal_groups'

    def method(self):
        return 'POST'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def test_upsertSellableProductTerminalGroupSuccessfully(self):
        sellable_product = fake.sellable_product(seller_id=fake.seller().id, editing_status_code='inactive')
        fake.sellable_product_terminal_group(
            terminal_group=self.terminal_groups[0],
            sellable_product=sellable_product
        )

        code, body = self.call_api(
            url=self.url(),
            data=self.data
        )

        self.assertEqual(code, 200)
        self.assertEqual(len(body['result']['sellableProducts']), 2)
        self.assertEqual(len(body['result']['terminalGroups']), 2)
        self.assertEqual(sellable_product.editing_status_code, 'inactive')

        result = models.SellableProductTerminalGroup.query.all()
        self.assertEqual(len(result), 5)

        result = models.SellableProductTerminalGroup.query.filter(
            models.SellableProductTerminalGroup.sellable_product_id.in_(self.data['sellableProducts']),
        ).all()

        self.assertEqual(len(result), 4)
        for r in result:
            self.assertIn(r.terminal_group_code, self.data['terminalGroups'])
            self.assertEqual(r.created_by, self.user.email)
            self.assertEqual(r.updated_by, self.user.email)

        self.mock_signal.assert_called()
