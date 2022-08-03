import logging
from catalog import models

__author__ = 'Quang.LM'

from catalog.models import SellableProductSeoInfoTerminal
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
import catalog.models as m

_logger = logging.getLogger(__name__)


class GetSellableProductUrlKeySEOInfoOnTerminal(APITestCase):
    ISSUE_KEY = 'CATALOGUE-413'
    FOLDER = '/SellableProductTerminal/UrlKey/Get'

    def init_sellable_product(self):
        self.product_variant = fake.product_variant()
        self.init_data(variant_id=self.product_variant.id, add_seo=True)

    def init_data(self, variant_id=None, add_seo=True):
        self.sellable_product = fake.sellable_product(
            seller_id=self.user.seller_id, variant_id=variant_id)

        self.terminal = fake.terminal(
            seller_id=self.user.seller_id,
            sellable_ids=[self.sellable_product.id],
            add_seo=add_seo,
            is_active=True
        )
        fake.seller_terminal(seller_id=self.user.seller_id,
                             terminal_id=self.terminal.id)

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.init_data()

    def method(self):
        return 'GET'

    def url_params(self):
        return '?terminalCodes={}'

    def url(self):
        return '/sellable_products/{}/terminals/seo_info'

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            return super().call_api(data, content_type, method, url)

    def test_200_getUrlKeySEOInfoSuccessfully_WithDataFromSeo(self):
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format(self.terminal.code))

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == self.sellable_product.id).first()

        result = body['result']

        self.assertEqual(code, 200)
        self.assertIsNotNone(body['result'])
        self.assertEqual(result.get('urlKey'), product.url_key)

    def test_200_getUrlKeySEOInfoSuccessfully_WithNoData(self):
        self.init_sellable_product()
        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == self.sellable_product.id).first()
        product.url_key = None
        models.db.session.commit()

        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format(self.terminal.code))

        result = body['result']

        self.assertEqual(code, 200)
        self.assertIsNotNone(body['result'])
        self.assertIsNone(result.get('urlKey'))
