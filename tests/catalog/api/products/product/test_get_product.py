# coding=utf-8
import contextlib

from tests.catalog.api import APITestCase
from catalog.api.product.product import schema
from tests.faker import fake
from tests import logged_in_user


class GetGenericProductTestCase(APITestCase):
    # ISSUE_KEY = 'SC-388'
    ISSUE_KEY = 'SC-550'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)

    def method(self):
        return 'GET'

    def url(self):
        return '/products/{}'

    def assertProduct(self, data, product):
        real_data = schema.GenericProduct().dump(product)
        for key, value in data.items():
            assert value == real_data[key]

    def test_passProductOwnedByUser__returnProduct(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id))
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assertProduct(body['result'], self.product)

    def test_passProductNotExist__raiseBadRequestException(self):
        product_id = fake.random_int(min=1000)
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product_id))
        assert 400 == code
        assert body['message'] == f'Không tồn tại sản phẩm có id là {product_id}'

    def test_passProductOwnedByOtherSeller__pass(self):
        product = fake.product(created_by=fake.iam_user().email, editing_status_code='draft')
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product.id))
        assert 200 == code

    def test_passApprovedProductOwnedByOtherUser__returnProduct(self):
        product = fake.product(created_by=fake.iam_user().email, editing_status_code='approved')
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product.id))
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assertProduct(body['result'], product)
