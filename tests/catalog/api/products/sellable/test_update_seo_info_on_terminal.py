import logging

__author__ = 'Minh.ND'

from copy import deepcopy

from mock import patch

from catalog import models
from catalog.models import SellableProductSeoInfoTerminal
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

_logger = logging.getLogger(__name__)


class UpdateAndInsertSellableProductSEOInfoOnTerminal(APITestCase):
    ISSUE_KEY = 'CATALOGUE-865'
    FOLDER = '/Sellable/SEOInfo'

    def method(self):
        return 'PUT'

    def url(self):
        return '/sellable_products/{}/terminals/seo_info'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.sellable_update_seo_info_signal.send')
        self.mock_signal = self.patcher.start()

        self.user = fake.iam_user()

        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)

        self.terminals = [
            fake.terminal(
                seller_id=self.user.seller_id,
                sellable_ids=[self.sellable_product.id],
                is_active=True
            ),
            fake.terminal(
                seller_id=self.user.seller_id,
                sellable_ids=[self.sellable_product.id],
                is_active=True
            )
        ]
        self.seller_terminals = [
            fake.seller_terminal(seller_id=self.user.seller_id, terminal_id=self.terminals[0].id),
            fake.seller_terminal(seller_id=self.user.seller_id, terminal_id=self.terminals[1].id)
        ]

        self.data = {
            "terminalCodes": [self.terminals[0].code, self.terminals[1].code],
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

    def test_updateAndInsertSEOInfoSuccessfully(self):
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        for terminal in self.terminals:
            seo_info = SellableProductSeoInfoTerminal.query.filter_by(
                sellable_product_id=self.sellable_product.id,
                terminal_code=0
            ).first()

            product = models.Product.query.filter(models.Product.id == models.SellableProduct.product_id,
                                                  models.SellableProduct.id == seo_info.sellable_product_id).first()

            self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
            self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
            self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
            self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
            self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
            self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
            self.assertEqual(self.user.email, seo_info.updated_by)
            self.assertNotEqual(self.user.email, seo_info.created_by)

        self.mock_signal.assert_called_once()

    def test_passViolatedMaxLengthRule__returnBadRequest(self):
        data = deepcopy(self.data)
        data['seoInfo']['displayName'] = ''.join(['x' for x in range(266)])
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

        data = deepcopy(self.data)
        data['terminalCodes'].append(''.join(['x' for x in range(50)]))
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

        data = deepcopy(self.data)
        data['seoInfo']['description'] = ''.join(['x' for x in range(10001)])
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 200)

    def test_passEmptySeoInfo__returnBadRequest(self):
        data = self.data.copy()
        data['seoInfo'] = {}
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_passEmptyTerminals__returnBadRequest(self):
        data = self.data.copy()
        data['terminalCodes'] = []
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

        self.mock_signal.assert_not_called()

    def test_passEmptyTerminalValue__returnBadRequest(self):
        data = self.data.copy()
        data['terminalCodes'].append('')
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_passEmptyPayload(self):
        data = {}
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)
        self.mock_signal.assert_not_called()

    def test_passViolateSpecialCharacterSeoName__returnBadRequest(self):
        data = self.data.copy()
        data['seoInfo']['displayName'] = 'seo*name'
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=data)
        self.assertEqual(code, 400)

    def test_passNonExistSellableProductId__returnBadRequest(self):
        code, body = self.call_api(url=self.url().format(123), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không tồn tại')

    def test_passNonExistTerminalsCode__returnBadRequest(self):
        self.data['terminalCodes'].append('CP0001')

        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Điểm bán không tồn tại')
        self.mock_signal.assert_not_called()

    def test_passInactiveTerminals__returnBadRequest(self):
        self.data['terminalCodes'].append(fake.terminal(is_active=False).code)

        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Điểm bán không tồn tại')
        self.mock_signal.assert_not_called()

    def test_passNotSellableProductOfSeller__returnBadReqest(self):
        sellable_product = fake.sellable_product()

        code, body = self.call_api(url=self.url().format(sellable_product.id), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không thuộc về seller')
        self.mock_signal.assert_not_called()

    def test_passNotTerminalCodesOfSellerCanSellingOn__returnBadRequest(self):
        self.data['terminalCodes'].append(fake.terminal(is_active=True).code)

        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Seller không được phép xem hoặc thêm thông tin SEO ở điểm bán này')
        self.mock_signal.assert_not_called()

    def test_updateAndInsertSEOInfoForAllTerminalSuccessfully(self):
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id, is_seo=False)
        del self.data['terminalCodes']
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_id=0
        ).first()

        product = models.Product.query.filter(models.Product.id == models.SellableProduct.product_id,
                                              models.SellableProduct.id == seo_info.sellable_product_id).first()

        self.assertIsNotNone(seo_info)
        self.assertEqual(self.data['seoInfo'].get('displayName'), product.display_name)
        self.assertEqual(self.data['seoInfo'].get('metaTitle'), product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(self.user.email, seo_info.created_by)
        models.db.session.commit()

        self.data['seoInfo']['displayName'] = None
        self.data['seoInfo']['metaTitle'] = ''
        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)
        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])
        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_id=0
        ).first()
        self.assertIsNotNone(seo_info)
        self.assertIsNone(product.display_name)
        self.assertEqual(product.meta_title, '')

        self.data = {
            "seoInfo": {
                "metaDescription": fake.text(),
                "metaKeyword": fake.text(),
                "shortDescription": fake.text(),
                "urlKey": fake.text()
            }
        }

        original_seo_info = {
            'description': deepcopy(seo_info.description),
        }

        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_id=0
        ).first()

        self.assertIsNotNone(seo_info)
        self.assertIsNone(product.display_name)
        self.assertEqual(product.meta_title, '')
        self.assertEqual(original_seo_info.get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)

    def test_updateSEOInfoWithMissingFields__returnSuccessfully(self):
        self.data['terminalCodes'] = [self.terminals[0].code]
        del self.data['seoInfo']['metaTitle']
        del self.data['seoInfo']['displayName']

        original_seo_info = deepcopy(SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first())

        original_product = models.Product.query.filter(
            models.Product.id == models.SellableProduct.product_id,
            models.SellableProduct.id == original_seo_info.sellable_product_id
        ).first()
        original_display_name = original_product.display_name
        original_meta_title = original_product.meta_title

        code, body = self.call_api(url=self.url().format(self.sellable_product.id), data=self.data)

        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = original_product

        self.assertIsNotNone(seo_info)
        self.assertEqual(original_display_name, product.display_name)
        self.assertEqual(original_meta_title, product.meta_title)
        self.assertEqual(self.data['seoInfo'].get('metaDescription'), product.meta_description)
        self.assertEqual(self.data['seoInfo'].get('metaKeyword'), product.meta_keyword)
        self.assertEqual(self.data['seoInfo'].get('description'), seo_info.description)
        self.assertEqual(self.data['seoInfo'].get('shortDescription'), seo_info.short_description)
        self.assertEqual(self.user.email, seo_info.updated_by)
        self.assertEqual(original_seo_info.created_by, seo_info.created_by)

    def test_200_updateAndInsertSEOInfoBySku_successfully(self):
        code, body = self.call_api(url=self.url().format('sku/' + self.sellable_product.sku), data=self.data)
        self.assertEqual(code, 200)
        self.assertEqual(body['message'], "Thêm thông tin SEO thành công")
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = models.Product.query.filter(models.Product.id == models.SellableProduct.product_id,
                                              models.SellableProduct.id == seo_info.sellable_product_id).first()

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
