# coding=utf-8

from tests.catalog.api import APITestCase
from catalog.api.product.product import schema
from tests.faker import fake
from tests import logged_in_user


class GetHistoryProductTestCase(APITestCase):
    # ISSUE_KEY = 'SC-388'
    ISSUE_KEY = 'CATALOGUE-865'
    FOLDER = '/Products/history'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellableProduct = fake.sellable_product(seller_id=self.seller.id)
        self.productHistory = fake.product_hisotry(sellableProduct=self.sellableProduct)

    def method(self):
        return 'GET'

    def url(self):
        return '/products/history/{}'

    def assertProductHistory(self, data, productHistory):
        real_data = schema.ProductHistory().dump({"histories": [productHistory]})
        for key, value in data.items():
            assert value == real_data[key]

    def test_passProductHistory__returnProductLog(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.sellableProduct.id))
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assertProductHistory(body['result'], self.productHistory)

    def test_NotExistedProductId__Raise404Notfound(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(fake.id()))
        assert 404 == code
        assert body['message'] == "Không tìm thấy sản phẩm, hoặc sản phẩm không nằm trong seller của bạn"

    def test_DifferentSellerId__Raise404Notfound(self):
        self.user.seller_id = fake.id()
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(fake.id()))
        assert 404 == code
        assert body['message'] == "Không tìm thấy sản phẩm, hoặc sản phẩm không nằm trong seller của bạn"


class GetHistorySkuTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-865'
    FOLDER = '/Products/history'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellableProduct = fake.sellable_product(seller_id=self.seller.id)
        self.productHistory = fake.product_hisotry(sellableProduct=self.sellableProduct)

    def method(self):
        return 'GET'

    def url(self):
        return '/skus/{}/history'

    def assertProductHistory(self, data, productHistory):
        real_data = schema.ProductHistory().dump({"histories": [productHistory]})
        for key, value in data.items():
            assert value == real_data[key]

    def test_200_bySku_returnProductLog(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.sellableProduct.sku))
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assertProductHistory(body['result'], self.productHistory)
