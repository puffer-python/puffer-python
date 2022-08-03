import logging

__author__ = 'Minh.ND'

from catalog.models import SellableProductSeoInfoTerminal
import catalog.models as m
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

_logger = logging.getLogger(__name__)


class GetSellableProductSEOInfoOnTerminal(APITestCase):
    ISSUE_KEY = 'CATALOGUE-865'
    FOLDER = '/Sellable/SEOInfo'

    def method(self):
        return 'GET'

    def url(self):
        return '/sellable_products/{}/terminals/seo_info'

    def url_params(self):
        return '?terminalCodes={}'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)
        self.terminal = fake.terminal(
            seller_id=self.user.seller_id,
            sellable_ids=[self.sellable_product.id],
            is_active=True
        )
        self.seller_terminal = fake.seller_terminal(seller_id=self.user.seller_id, terminal_id=self.terminal.id)

    def test_getSEOInfoSuccessfully(self):
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format(self.terminal.code))

        self.assertEqual(code, 200)
        self.assertIsNotNone(body['result'])

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == self.sellable_product.id).first()

        result = body['result']

        self.assertEqual(result.get('displayName'), product.display_name)
        self.assertEqual(result.get('metaTitle'), product.meta_title)
        self.assertEqual(result.get('metaDescription'), product.meta_description)
        self.assertEqual(result.get('metaKeyword'), product.meta_keyword)
        self.assertEqual(result.get('urlKey'), product.url_key)

    def test_getSEOInfoViolatedMaxLength__returnBadRequest(self):
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format('A' * 100)
        )
        self.assertEqual(code, 400)

    def test_passNonExistSellableProductId__returnBadRequest(self):
        code, body = self.call_api(url=self.url().format(123) + self.url_params().format(self.terminal.code))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không tồn tại')

    def test_passNonExistTerminalCode__returnBadRequest(self):
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format('VNM_OLN_WEB_0001'))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Điểm bán không tồn tại')

    def test_passInactiveTerminal__returnBadRequest(self):
        inactive_terminal = fake.terminal(is_active=False)
        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format(inactive_terminal.code))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Điểm bán không tồn tại')

    def test_passNotSellableProductOfSeller__returnBadReqest(self):
        sellable_product = fake.sellable_product()

        code, body = self.call_api(
            url=self.url().format(sellable_product.id) + self.url_params().format(self.terminal.code))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Sản phẩm không thuộc về seller')

    def test_passNotTerminalCodeOfSellerCanSellingOn__returnBadRequest(self):
        terminal = fake.terminal(is_active=True)

        code, body = self.call_api(
            url=self.url().format(self.sellable_product.id) + self.url_params().format(terminal.code))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Seller không được phép xem hoặc thêm thông tin SEO ở điểm bán này')

    def test_200_getBySku_successfully(self):
        code, body = self.call_api(
            url=self.url().format('sku/'+self.sellable_product.sku))
        self.assertEqual(code, 200)
        self.assertIsNotNone(body['result'])

        seo_info = SellableProductSeoInfoTerminal.query.filter_by(
            sellable_product_id=self.sellable_product.id,
            terminal_code=0
        ).first()

        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == seo_info.sellable_product_id).first()

        result = body['result']

        self.assertEqual(result.get('displayName'), product.display_name)
        self.assertEqual(result.get('metaTitle'), product.meta_title)
        self.assertEqual(result.get('metaDescription'), product.meta_description)
        self.assertEqual(result.get('metaKeyword'), product.meta_keyword)
        self.assertEqual(result.get('urlKey'), product.url_key)
