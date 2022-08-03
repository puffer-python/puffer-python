from tests.catalog.api import APIBaseTestCase, APITestCaseWithMysqlByFunc, APITestCase
from tests import logged_in_user
from tests.faker import fake
import catalog.models as m

__author__ = 'long.t'

class GetSeoInfoTestCases(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1729'
    FOLDER = '/Sellable/Sku/SEOInfo'

    def method(self):
        return 'GET'

    def url(self):
        return '/sellable_products/sku/{}/terminals/seo_info'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_product = fake.sellable_product(seller_id=self.user.seller_id)


    def test_get_seo_info_return_200_success(self):
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku))
        product = m.Product.query.filter(m.Product.id == m.SellableProduct.product_id,
                                         m.SellableProduct.id == self.sellable_product.id).first()

        self.assertEqual(code, 200)
        self.assertEqual(body['result']['displayName'], product.display_name)
        self.assertEqual(body['result']['metaTitle'], product.meta_title)
        self.assertEqual(body['result']['metaDescription'], product.meta_description)
        self.assertEqual(body['result']['metaKeyword'], product.meta_keyword)
        self.assertEqual(body['result']['urlKey'], product.url_key)

    def test_get_seo_info_return_400_when_not_exist_product(self):
        self.sellable_product.product_id = fake.integer()
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku))
        self.assertEqual(code, 400)

        code, body = self.call_api(url=self.url().format(fake.integer()))

        self.assertEqual(code, 400)

    def test_get_seo_info_return_400_when_product_not_belong_to_seller(self):
        self.sellable_product = fake.sellable_product()
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku))

        self.assertEqual(code, 400)

    def test_get_seo_info_return_200_when_no_seo_info_in_product(self):
        self.product = fake.product(is_seo=False)
        self.sellable_product.product = self.product
        code, body = self.call_api(url=self.url().format(self.sellable_product.sku))

        self.assertEqual(code, 200)
        self.assertIsNotNone(body['result'])
        self.assertIsNone(body['result']['displayName'])
        self.assertIsNone(body['result']['metaTitle'])
        self.assertIsNone(body['result']['metaDescription'])
        self.assertIsNone(body['result']['metaKeyword'])
        self.assertIsNone(body['result']['urlKey'])