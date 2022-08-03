import logging

__author__ = 'long.t'

from copy import deepcopy

from mock import patch

from catalog.models import SellableProductSeoInfoTerminal
import catalog.models as m
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

_logger = logging.getLogger(__name__)


class UpdateAndInsertSellableProductSEOInfo(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1728'
    FOLDER = '/Sellable/Sku/SEOInfo'

    def method(self):
        return 'PUT'

    def url(self):
        return '/sellable_products/sku/{}/terminals/seo_info'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.sellable_update_seo_info_signal.send')
        self.mock_signal = self.patcher.start()

        self.user = fake.iam_user()

        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)

        self.data = {
            "seoInfo": {
                "displayName": fake.text() + 'Aa/,.(-_&)1 Séo name' + fake.text(),
                "metaTitle": fake.text(),
                "metaDescription": fake.text(),
                "metaKeyword": fake.text(),
                "description": fake.text(),
                "shortDescription": fake.text(),
                "urlKey": fake.text()
            }
        }

    def test_update_seo_info_return_success_update_seo_product_layer(self):
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
        self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('urlKey'), product.url_key)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertNotEqual(self.user.email, seo_info.created_by)

        self.mock_signal.assert_called_once()

    def test_update_seo_info_return_400_when_violated_max_length_rule(self):
        data = deepcopy(self.data)
        data['seoInfo']['description'] = ''.join(['x' for _ in range(10001)])
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=data)
        self.assertEqual(code, 200)

        data = deepcopy(self.data)
        data['seoInfo']['displayName'] = ''.join(['x' for _ in range(266)])
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=data)
        self.assertEqual(code, 400)

    def test_update_seo_info_return_400_when_passing_empty_seo_info(self):
        data = self.data.copy()
        data['seoInfo'] = {}
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=data)
        self.assertEqual(code, 400)

    def test_update_seo_info_return_400_when_passing_empty_payload(self):
        data = {}
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=data)
        self.assertEqual(code, 400)
        self.mock_signal.assert_not_called()

    def test_update_seo_data_return_400_when_passing_special_character_in_display_name(self):
        data = self.data.copy()
        data['seoInfo']['displayName'] = 'seo*name'
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=data)
        self.assertEqual(code, 400)

    def test_update_seo_data_info_return_400_when_passing_non_exist_sellable_product_id(self):
        self.sellable_product.product_id = fake.integer()
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không tồn tại')

        code, body = self.call_api(url=self.url().format(123), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không tồn tại')

    def test_update_seo_info_return_400_when_passing_sellable_product_id_not_belong_to_seller(self):
        sellable_product = fake.sellable_product()

        code, body = self.call_api(url=self.url().format(sellable_product.sku), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không thuộc về seller')
        self.mock_signal.assert_not_called()

    def test_update_seo_info_return_200_when_passing_missing_field_display_name(self):
        del self.data['seoInfo']['displayName']

        original_seo_info = deepcopy(SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first())

        original_product_display_name = m.Product.query.filter(
            m.Product.id == m.SellableProduct.product_id,
            m.SellableProduct.id == original_seo_info.sellable_product_id
        ).first().display_name
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertIsNotNone(seo_info)
        self.assertEqual(original_product_display_name, product.display_name)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(original_seo_info.created_by, seo_info.created_by)

    def test_update_seo_info_return_200_when_passing_missing_field_meta_title(self):
        del self.data['seoInfo']['metaTitle']

        original_seo_info = deepcopy(SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first())

        original_product_meta_title = m.Product.query.filter(
            m.Product.id == m.SellableProduct.product_id,
            m.SellableProduct.id == original_seo_info.sellable_product_id
        ).first().meta_title
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertIsNotNone(seo_info)
        self.assertEqual(original_product_meta_title, product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(original_seo_info.created_by, seo_info.created_by)

    def test_update_seo_info_return_200_when_passing_missing_field_meta_description(self):
        del self.data['seoInfo']['metaDescription']

        original_seo_info = deepcopy(SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first())

        original_product_meta_description = m.Product.query.filter(
            m.Product.id == m.SellableProduct.product_id,
            m.SellableProduct.id == original_seo_info.sellable_product_id
        ).first().meta_description
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertIsNotNone(seo_info)
        self.assertEqual(original_product_meta_description, product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(original_seo_info.created_by, seo_info.created_by)

    def test_update_seo_info_return_200_when_passing_missing_field_meta_keyword(self):
        del self.data['seoInfo']['metaKeyword']

        original_seo_info = deepcopy(SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first())

        original_product_meta_keyword = m.Product.query.filter(
            m.Product.id == m.SellableProduct.product_id,
            m.SellableProduct.id == original_seo_info.sellable_product_id
        ).first().meta_keyword
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertIsNotNone(seo_info)
        self.assertEqual(original_product_meta_keyword, product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(original_seo_info.created_by, seo_info.created_by)

    def test_update_seo_info_return_400_when_passing_missing_field_url_key(self):
        del self.data['seoInfo']['urlKey']
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku), data=self.data)

        self.assertEqual(code, 400)
