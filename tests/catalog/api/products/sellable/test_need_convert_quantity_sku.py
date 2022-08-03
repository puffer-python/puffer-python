# coding=utf-8
import logging
import random

from mock import patch
from catalog import utils, models
from catalog.api.product.sellable import schema
from catalog.services.products.sellable import create_sellable_products
from catalog.utils.lambda_list import LambdaList
from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user

__author__ = 'Chung.HD'
_logger = logging.getLogger(__name__)


def url_params(params):
    import urllib
    query = urllib.parse.urlencode(params)
    return query


class NeedConvertQuantitySKUTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-589'
    FOLDER = '/Sellable/Uom'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.other_seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id, seller_ids='%s,%s' % (self.seller.id, self.other_seller.id))
        self.product = fake.product(created_by=self.user.email)
        uom_attr = fake.uom_attribute(attribute_set_id=self.product.attribute_set_id)
        uom_options_value = [uom_attr.options[0].id, uom_attr.options[1].id, uom_attr.options[1].id, ]
        uom_ratios_value = [random.randint(2, 100), 1, random.randint(2, 100)]
        self.variants = [
            fake.product_variant(product_id=self.product.id, uom_attr=uom_attr, uom_option_value=uom_options_value[i],
                                 uom_ratio_value=uom_ratios_value[i])
            for i in range(3)]
        self.shipping_types = [fake.shipping_type() for _ in range(2)]

        price = fake.integer(max=1000000000)
        self.sellable_products_data = [{
            'variantId': self.variants[i].id,
            'sellerSku': utils.random_string(12),
            'barcode': utils.random_string(10),
            'supplierSalePrice': price,
            'partNumber': fake.text(),
            'providerId': 1,
            'allowSellingWithoutStock': random.choice([True, False]),
            'manageSerial': random.choice([True, False]),
            'expiryTracking': random.choice([True, False]),
            'expirationType': random.choice([1, 2]),
            'daysBeforeExpLock': random.randint(1, 10000),
            'shippingTypes': [self.shipping_types[0].id, self.shipping_types[1].id]
        } for i in range(3)]
        for data in self.sellable_products_data:
            data['autoGenerateSerial'] = False if not data['manageSerial'] \
                else random.choice([True, False])
        data = {
            'productId': self.product.id,
            'sellableProducts': self.sellable_products_data
        }

        self.data = schema.SellableProductsRequest().load(data)

    def url(self):
        return '/sellable_products/uom_info'

    def query_with(self, params):
        url = "{url}?{query_string}".format(url=self.url(), query_string=url_params(params))
        return self.call_api(url=url)

    def method(self):
        return 'GET'

    def test_createSkuWithOneUOM__needConverQty_equal_0(self):
        self.data['sellable_products'] = self.data['sellable_products'][:1]
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            assert skus[0].need_convert_qty == 0

    def test_createSkuWithDifferentUOMCode__needConverQty_equal_0(self):
        self.data['sellable_products'] = self.data['sellable_products'][:2]
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            assert skus[0].need_convert_qty == 0
            assert skus[1].need_convert_qty == 0

    def test_createSkuWithSameUOMCode__needConverQty_equal_1(self):
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            assert skus[0].need_convert_qty == 0
            assert skus[1].need_convert_qty == 1
            assert skus[2].need_convert_qty == 1

    def test_getUomInfoSkuWithSameUOMCode_restrictConvertQty_equal_1__needConverQty_equal_1_only_return_SKU_With_Ratio_not_equal_1(
            self):
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            skus = LambdaList(skus).map(lambda x: x.sku).string_join(',')
            params = {
                'skus': skus,
                'restrictConvertQty': 1
            }
            code, body = self.query_with(params=params)
            assert code == 200, body
            assert body, body
            assert body['result']['skus'], body
            for sku in body['result']['skus']:
                assert sku['needConvertQty'] == 0 or (sku['needConvertQty'] == 1 and sku['uomRatio'] != 1)

    def test_getUomInfoSkuWithDifferentUOMCode_restrictConvertQty_equal_1__return_SKU_with_needConverQty_equal_0(self):
        self.data['sellable_products'] = self.data['sellable_products'][:2]
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            skus = LambdaList(skus).map(lambda x: x.sku).string_join(',')
            params = {
                'skus': skus,
                'restrictConvertQty': 1
            }
            code, body = self.query_with(params=params)
            assert code == 200, body
            assert body, body
            assert body['result']['skus'], body
            for sku in body['result']['skus']:
                assert sku['needConvertQty'] == 0 or (sku['needConvertQty'] == 1 and sku['uomRatio'] != 1)

    def test_getUomInfoSku__return_Field_uomName(self):
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            skus = LambdaList(skus).map(lambda x: x.sku).string_join(',')
            params = {
                'skus': skus
            }
            code, body = self.query_with(params=params)
            assert code == 200, body
            assert body, body
            assert body['result']['skus'], body
            for sku in body['result']['skus']:
                assert sku['uomName']
                assert sku.get('needConvertQty', None) != None

    def test_getUomInfoSkuWithSellerIdEqual0__return_sku_of_all_sellers(self):
        other_user = fake.iam_user(seller_id=self.other_seller.id)
        with logged_in_user(other_user):
            other_skus, msg = create_sellable_products(self.data)
        with logged_in_user(self.user):
            skus, msg = create_sellable_products(self.data)
            assert msg == 'Tạo SKU thành công'
            assert skus
            skus = LambdaList(other_skus + skus).map(lambda x: x.sku).string_join(',')
            params = {
                'skus': skus,
                'sellerId': 0
            }
            code, body = self.query_with(params=params)
            assert code == 200, body
            assert body, body
            assert body['result']['skus'], body
            exist_other_seller_sku = False
            for sku in body['result']['skus']:
                assert sku['uomName']
                assert sku.get('needConvertQty', None) != None
                if sku['sellerId'] != self.user.seller_id:
                    exist_other_seller_sku = True

            assert exist_other_seller_sku
