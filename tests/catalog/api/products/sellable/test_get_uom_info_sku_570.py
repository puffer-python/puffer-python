import logging
import random

__author__ = 'Minh.ND'

from catalog.models import SellableProductSeoInfoTerminal
from catalog.utils.lambda_list import LambdaList
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests.utils import PAGE_OUT_OF_RANGE, PAGE_SIZE_OUT_OF_RANGE

_logger = logging.getLogger(__name__)


def url_params(params):
    import urllib
    query = urllib.parse.urlencode(params)
    return query


class GetUomInfoSkuTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-570'
    FOLDER = '/SellableProduct/UOMInfo/Get_570'

    def method(self):
        return 'GET'

    def url(self):
        return '/sellable_products/uom_info'

    def query_with(self, params):
        url = "{url}?{query_string}".format(url=self.url(), query_string=url_params(params))
        return self.call_api_with_login(url=url)

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_products = [fake.sellable_product(seller_id=self.user.seller_id, uom_code=fake.unique_str(),
                                                        uom_ratio=fake.float(max=10)) for _ in range(5)]

    def test_return200__matchName(self):
        skus = LambdaList(self.sellable_products).map(lambda x: x.sku).string_join(',')
        params = {
            'skus': skus
        }
        code, body = self.query_with(params=params)
        for index, sku in enumerate(body['result']['skus']):
            entity = LambdaList(self.sellable_products).filter(lambda x: x.sku == sku['sku']).first()
            self.assertEqual(entity.name, sku['name'])


