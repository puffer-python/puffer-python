# coding=utf-8
import logging
from mock import patch

from catalog.models import SellableProductSeoInfoTerminal
import catalog.models as m
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class UpdateUrlKeySellableProductTerminalTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-412'
    FOLDER = '/SellableProductTerminal/UrlKey/Update'

    def init_data(self, add_seo=True):
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)

        self.terminals = [
            fake.terminal(
                seller_id=self.user.seller_id,
                sellable_ids=[self.sellable_product.id],
                add_seo=add_seo,
                is_active=True
            ),
            fake.terminal(
                seller_id=self.user.seller_id,
                sellable_ids=[self.sellable_product.id],
                add_seo=add_seo,
                is_active=True
            )
        ]
        self.seller_terminals = [
            fake.seller_terminal(seller_id=self.user.seller_id, terminal_id=self.terminals[0].id),
            fake.seller_terminal(seller_id=self.user.seller_id, terminal_id=self.terminals[1].id)
        ]

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.sellable_update_seo_info_signal.send')
        self.mock_signal = self.patcher.start()

        self.user = fake.iam_user()
        self.init_data()

    def method(self):
        return 'PUT'

    def url(self):
        return '/sellable_products/{}/terminals/seo_info'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def test_400_invalidNotInPayload__returnBadRequest(self):
        data = {
            'terminalCodes': [self.terminals[0].code, self.terminals[1].code],
            'seoInfo': {
                'displayName': fake.text(),
                'metaTitle': fake.text(),
                'metaDescription': fake.text(),
                'metaKeyword': fake.text(),
                'description': fake.text(),
                'shortDescription': fake.text()
            }
        }
        code, _ = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_400_invalidEmpty__returnBadRequest(self):
        data = {
            'terminalCodes': [self.terminals[0].code, self.terminals[1].code],
            'seoInfo': {
                'displayName': fake.text(),
                'metaTitle': fake.text(),
                'metaDescription': fake.text(),
                'metaKeyword': fake.text(),
                'description': fake.text(),
                'shortDescription': fake.text(),
                'urlKey': ''
            }
        }
        code, _ = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_400_invalidAllSpaces__returnBadRequest(self):
        data = {
            'terminalCodes': [self.terminals[0].code, self.terminals[1].code],
            'seoInfo': {
                'displayName': fake.text(),
                'metaTitle': fake.text(),
                'metaDescription': fake.text(),
                'metaKeyword': fake.text(),
                'description': fake.text(),
                'shortDescription': fake.text(),
                'urlKey': '     '
            }
        }
        code, _ = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_400_invalidFormatWithNotAllowedCharacters__returnBadRequest(self):
        url_keys = [
            'abc123@',
            'abc123_',
            'abc123美丽',
        ]
        for url_key in url_keys:
            data = {
                'terminalCodes': [self.terminals[0].code, self.terminals[1].code],
                'seoInfo': {
                    'displayName': fake.text(),
                    'metaTitle': fake.text(),
                    'metaDescription': fake.text(),
                    'metaKeyword': fake.text(),
                    'description': fake.text(),
                    'shortDescription': fake.text(),
                    'urlKey': url_key
                }
            }
            code, _ = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
            self.assertEqual(code, 400)

    def test_200_validData_addNew__returnSuccess(self):
        self.init_data(add_seo=False)
        data = {
            'seoInfo': {
                'displayName': fake.text(),
                'metaTitle': fake.text(),
                'metaDescription': fake.text(),
                'metaKeyword': fake.text(),
                'description': fake.text(),
                'shortDescription': fake.text(),
                'urlKey': 'abc123-sản-phẩm'
            }
        }
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)

        seo_info1 = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == self.sellable_product.product_id).first()

        self.assertEqual(code, 200)

        self.assertIsNotNone(seo_info1)
        self.assertEqual(product.url_key, 'abc123-sản-phẩm')

    def test_200_validData_update__returnSuccess(self):
        data = {
            'seoInfo': {
                'displayName': fake.text(),
                'metaTitle': fake.text(),
                'metaDescription': fake.text(),
                'metaKeyword': fake.text(),
                'description': fake.text(),
                'shortDescription': fake.text(),
                'urlKey': 'abc123-sản-phẩm'
            }
        }
        code, _ = self.call_api(url=self.url().format(self.sellable_product.id), data=data)

        product = m.Product.query.filter(m.Product.id == self.sellable_product.product_id).first()

        self.assertEqual(code, 200)
        self.assertIsNotNone(product)
        self.assertEqual(product.url_key, 'abc123-sản-phẩm')
