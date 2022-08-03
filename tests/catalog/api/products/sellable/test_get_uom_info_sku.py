import logging
import random

__author__ = 'Minh.ND'

from catalog.models import SellableProductSeoInfoTerminal
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests.utils import PAGE_OUT_OF_RANGE, PAGE_SIZE_OUT_OF_RANGE

_logger = logging.getLogger(__name__)


class GetUomInfoSkuTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-393'
    FOLDER = '/SellableProduct/UOMInfo/Get'

    def method(self):
        return 'GET'

    def url(self):
        return '/sellable_products/uom_info'

    def url_params(self, params):
        import urllib
        query = urllib.parse.urlencode(params)
        return query

    def query_with(self, params):
        url = "{url}?{query_string}".format(url=self.url(), query_string=self.url_params(params))
        return self.call_api_with_login(url=url)

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_products = [fake.sellable_product(seller_id=self.user.seller_id, uom_code=fake.unique_str(), uom_ratio=fake.float(max=10)) for _ in range(30)]

    def test_getUOMInfo_BySKU_WithRatioField(self):
        skus = ','.join(sku.sku for sku in random.sample(self.sellable_products, k=random.randint(2,5)))
        params = {
            'skus': skus
        }
        code, body = self.query_with(params=params)
        for sku in body['result']['skus']:
            assert sku['uomCode']
            assert sku['uomRatio']

    def test_getUOMInfoBy_SellerSKU_WithRatioField(self):
        sellerSkus = ','.join(sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
        params = {
            'sellerSkus': sellerSkus
        }
        code, body = self.query_with(params=params)
        for sku in body['result']['skus']:
            assert sku['uomCode']
            assert sku['uomRatio']

    def test_getUOMInfoBy_SellerSKU_NotExist_ReturnEmpty(self):
        sellerSkus = ','.join(sku.seller_sku + 'a' for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
        params = {
            'sellerSkus': sellerSkus
        }
        code, body = self.query_with(params=params)
        assert len(body['result']['skus']) == 0

    def test_getUOMInfoBy_SKU_NotExist_ReturnEmpty(self):
        skus = ','.join(
            sku.sku + 'a' for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
        params = {
            'skus': skus
        }
        code, body = self.query_with(params=params)
        assert len(body['result']['skus']) == 0

    def test_return200__returnCorrectNumberOfItems(self):
        params = {
            'page': 1,
            'pageSize': 20,
            'skus': ','.join(sku.sku for sku in self.sellable_products)
        }

        code, body = self.query_with(params)
        self.assertEqual(200, code)
        self.assertEqual(params['pageSize'], len(body['result']['skus']))

    def test_return200__returnCorrectNumberOfItemsLessThanPageSize(self):
        k = random.randint(5,15)
        params = {
            'page': 1,
            'pageSize': 20,
            'skus': ','.join(sku.sku for sku in random.sample(self.sellable_products, k=k))
        }

        code, body = self.query_with(params)
        self.assertEqual(200, code)
        self.assertEqual(k, len(body['result']['skus']))

    def test_return200__returnCorrectNumberOfItemsLastPage(self):
        k = random.randint(22,30)
        params = {
            'page': 2,
            'pageSize': 20,
            'skus': ','.join(sku.sku for sku in random.sample(self.sellable_products, k=k))
        }

        code, body = self.query_with(params)
        self.assertEqual(200, code)
        self.assertEqual(k - 20, len(body['result']['skus']))

    def test_return400__pageOutOfRange(self):
        code, _ = self.query_with({
                'page': PAGE_OUT_OF_RANGE,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)

    def test_return400__pageNegative(self):
        code, _ = self.query_with({
                'page': -1,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)

    def test_return200__notPassingPageParam(self):
        # page default is 1 if absent
        code, body = self.query_with(
            {
                'pageSize': 20,
                'skus': ','.join(sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            }
        )
        self.assertEqual(200, code)

    def test_return400__pageEqualsZero(self):
        code, _ = self.query_with({
                'page': 0,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)

    def test_return400__pageSizeOutOfRange(self):
        code, _ = self.query_with({
                'pageSize': PAGE_SIZE_OUT_OF_RANGE,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)

    def test_return400__pageSizeNegative(self):
        code, _ = self.query_with({
                'pageSize': -1,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)

    def test_return200__notPassingPageSizeParam(self):
        # pageSize default is 10 if absent
        code, body = self.query_with(
            {
                'page': 1,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            }
        )
        self.assertEqual(200, code)

    def test_return400__pageSizeEqualsZero(self):
        code, _ = self.query_with({
                'pageSize': 0,
                'skus': ','.join(
                    sku.seller_sku for sku in random.sample(self.sellable_products, k=random.randint(2, 5)))
            })
        self.assertEqual(400, code)