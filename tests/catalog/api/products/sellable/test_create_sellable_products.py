# coding=utf-8
import logging
import random

from mock import patch
from catalog import utils
from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user
from catalog import models

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateSellableProductSellerSkuTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-541'
    FOLDER = '/Import/SellableSku'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.variants = [fake.product_variant(product_id=self.product.id)
                         for _ in range(3)]
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
        self.data = {
            'productId': self.product.id,
            'sellableProducts': self.sellable_products_data
        }

        self.patcher_signal = patch('catalog.services.products.sellable.signals.sellable_create_signal.send')
        self.mock_signal = self.patcher_signal.start()

    def tearDown(self):
        self.patcher_signal.stop()

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'POST'

    def assert_sellable_products(self, res):
        data = {e['sellerSku']: e for e in self.sellable_products_data}
        for product in res:
            product_data = data[product['sellerSku']]
            self.assertEqual(product['variantId'], product_data['variantId'])
            self.assertEqual(product['barcode'], product_data['barcode'])
            self.assertEqual(
                product['supplierSalePrice'],
                product_data['supplierSalePrice']
            )
            self.assertEqual(product['brand']['id'], self.product.brand_id)
            self.assertEqual(product['category']['id'], self.product.category_id)
            self.assertEqual(
                product['attributeSet']['id'],
                self.product.attribute_set_id
            )
            self.assertEqual(product['model'], self.product.model)
            self.assertEqual(
                product['warrantyMonths'],
                self.product.warranty_months
            )
            self.assertEqual(
                product['warrantyNote'],
                self.product.warranty_note
            )
            self.assertEqual(product['taxInCode'], self.product.tax_in_code)
            self.assertEqual(product['taxOutCode'], self.product.tax_out_code)
            self.assertEqual(
                product['allowSellingWithoutStock'],
                product_data['allowSellingWithoutStock']
            )
            self.assertEqual(
                product['manageSerial'],
                product_data['manageSerial']
            )
            self.assertEqual(
                product['autoGenerateSerial'],
                product_data['autoGenerateSerial']
            )
            self.assertEqual(
                product['expiryTracking'],
                product_data['expiryTracking']
            )
            self.assertEqual(
                product['expirationType'],
                product_data['expirationType']
            )
            self.assertEqual(
                product['daysBeforeExpLock'],
                product_data['daysBeforeExpLock']
            )

            self.assertEqual(len(product['shippingTypes']), 2)
            self.assertEqual(
                product['shippingTypes'][0]['id'],
                product_data['shippingTypes'][0],
            )
            self.assertEqual(
                product['shippingTypes'][1]['id'],
                product_data['shippingTypes'][1],
            )

    def test__ImportSKUWithMoreThan20Char__returnInvalidRequest(self):
        self.sellable_products_data[0]['sku'] = fake.text(length=30)
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test__SKUwithManualSellerSku__returnSuccessWithSellerSkuNotEqualSku(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code)
            self.assert_sellable_products(body['result'])
            for product in body['result']:
                assert product['sellerSku'] != product['sku']

    def test__SKUwithAutoGenSellerSku__returnSuccessWithSellerSkuEqualSku(self):
        for data in self.sellable_products_data:
            del data['sellerSku']
        self.seller.manual_sku = False
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)
            for product in body['result']:
                assert product['sellerSku'] == product['sku']

    def test__SKUwithManualSellerSku_NotPassingSellerSku__returnInvalidRequest(self):
        for data in self.sellable_products_data:
            del data['sellerSku']
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)

    def test__SKUwithAutoGenSellerSku_PassingSellerSku__returnInvalidRequest(self):
        self.seller.manual_sku = False
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)

    def test_passSKUWithSpecialCharacters__returnInvalidRequest(self):
        self.sellable_products_data[0]['sku'] = '㠰毥崯'
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)


class CreateUniqueSellableProduct(APITestCase):
    ISSUE_KEY = 'CATALOGUE-742'
    FOLDER = '/Import/SellableSku'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.fake_attribute_set(is_variation=0, name='Máy in')
        self.fake_uom(self.attribute_set)

        self.product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        self.variant = fake.product_variant(
            product_id=self.product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_cai.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_1.id
        )
        self.sellable_product = fake.sellable_product(
            seller_sku='123',
            variant_id=self.variant.id,
            uom_code=self.attr_option_cai.code,
            uom_ratio=self.attr_option_1.value,
            seller_id=self.seller.id
        )

        self.sellable_product_data = {
            'productId': self.product.id,
            'sellableProducts': [{
                'variantId': self.variant.id,
                'sellerSku': utils.random_string(12),
                'barcode': utils.random_string(10),
                'supplierSalePrice': fake.integer(max=1000000000),
                'partNumber': fake.text(),
                'providerId': 1,
                'allowSellingWithoutStock': random.choice([True, False]),
                'manageSerial': random.choice([True, False]),
                'expiryTracking': random.choice([True, False]),
                'expirationType': random.choice([1, 2]),
                'daysBeforeExpLock': random.randint(1, 10000),
                'autoGenerateSerial': False,
                'manageSerial': False
            }]
        }
        self.patcher_signal = patch('catalog.services.products.sellable.signals.sellable_create_signal.send')
        self.mock_signal = self.patcher_signal.start()

    def tearDown(self):
        self.patcher_signal.stop()

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'POST'

    def fake_attribute_set(self, is_variation=1, **kwargs):
        self.attribute_set = fake.attribute_set(**kwargs)
        self.attribute_group = fake.attribute_group(set_id=self.attribute_set.id)

        self.attribute_1 = fake.attribute(code='s1', value_type='selection', is_none_unit_id=True)
        self.attribute_2 = fake.attribute(code='s2', value_type='selection', is_none_unit_id=True)

        fake.attribute_group_attribute(attribute_id=self.attribute_1.id, group_ids=[self.attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=self.attribute_2.id, group_ids=[self.attribute_group.id],
                                       is_variation=is_variation)

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id)
        self.uom_attr = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        self.uom_ratio_attr = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        self.attr_option_cai = fake.attribute_option(self.uom_attr.id, value='Cái')
        self.attr_option_chiec = fake.attribute_option(self.uom_attr.id, value='Chiếc')
        self.attr_option_1 = fake.attribute_option(self.uom_ratio_attr.id, value='1')
        self.attr_option_2 = fake.attribute_option(self.uom_ratio_attr.id, value='2')

    def test_400_existed_SellerId_UOMCode_UOMRatio_SellerSku__returnInvalidRequest(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_cai.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_1.value
        )
        self.sellable_product_data['productId'] = product.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '123'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Sản phẩm 123 đã tồn tại')

    def test_200_existed_SellerId_UOMCode_SellerSku_Different_UOMRatio__createSuccessfully(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_cai.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_2.value
        )
        self.sellable_product_data['productId'] = product.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '123'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(200, code)
            self.assertIsNotNone(body['result'])

    def test_200_existed_SellerId_UOMCode_Different_UOMRatio_SellerSku__createSuccessfully(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_cai.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_2.value
        )
        self.sellable_product_data['productId'] = product.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '321'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(200, code)
            self.assertIsNotNone(body['result'])

    def test_200_existed_SellerId_UOMRatio_SellerSku_Different_UOMCode__createSuccessfully(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_chiec.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_1.value
        )
        self.sellable_product_data['productId'] = product.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '123'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(200, code)
            self.assertIsNotNone(body['result'])

    def test_200_existed_SellerId_UOMRatio_Different_UOMCode_SellerSku__createSuccessfully(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_chiec.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_1.value
        )
        self.sellable_product_data['productId'] = product.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '321'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(200, code)
            self.assertIsNotNone(body['result'])

    def test_200_existed_SellerId_SellerSku_Different_UOMCode_UOMRatio_createSucessfully(self):
        product = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant = fake.product_variant(
            product_id=product.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_chiec.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_1.value
        )
        sellable_product = fake.sellable_product(
            seller_sku='123',
            variant_id=variant.id,
            uom_code=self.attr_option_chiec.code,
            uom_ratio=self.attr_option_1.value
        )

        product_2 = fake.product(created_by=self.user.email, attribute_set_id=self.attribute_set.id)
        variant_2 = fake.product_variant(
            product_id=product_2.id,
            uom_attr=self.uom_attr,
            uom_option_value=self.attr_option_chiec.id,
            uom_ratio_attr=self.uom_ratio_attr,
            uom_ratio_value=self.attr_option_2.value
        )
        self.sellable_product_data['productId'] = product_2.id
        self.sellable_product_data['sellableProducts'][0]['variantId'] = variant_2.id
        self.sellable_product_data['sellableProducts'][0]['sellerSku'] = '123'

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.sellable_product_data)
            self.assertEqual(200, code)
            self.assertIsNotNone(body['result'])


class CreateSellableProductTestCase(APITestCase):
    ISSUE_KEY = 'SC-652'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.variants = [fake.product_variant(product_id=self.product.id)
                         for _ in range(3)]
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
            'shippingTypes': [self.shipping_types[0].id, self.shipping_types[1].id],
            'daysBeforeExpLock': random.randint(1, 10000)
        } for i in range(3)]
        for data in self.sellable_products_data:
            data['autoGenerateSerial'] = False if not data['manageSerial'] \
                else random.choice([True, False])
        self.data = {
            'productId': self.product.id,
            'sellableProducts': self.sellable_products_data
        }

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'POST'

    def assert_sellable_products(self, res):
        data = {e['sellerSku']: e for e in self.sellable_products_data}
        for product in res:
            product_data = data[product['sellerSku']]
            self.assertEqual(product['variantId'], product_data['variantId'])
            self.assertEqual(product['barcode'], product_data['barcode'])
            self.assertEqual(
                product['supplierSalePrice'],
                product_data['supplierSalePrice']
            )
            self.assertEqual(product['brand']['id'], self.product.brand_id)
            self.assertEqual(product['category']['id'], self.product.category_id)
            self.assertEqual(
                product['attributeSet']['id'],
                self.product.attribute_set_id
            )
            self.assertEqual(product['model'], self.product.model)
            self.assertEqual(
                product['warrantyMonths'],
                self.product.warranty_months
            )
            self.assertEqual(
                product['warrantyNote'],
                self.product.warranty_note
            )
            self.assertEqual(product['taxInCode'], self.product.tax_in_code)
            self.assertEqual(product['taxOutCode'], self.product.tax_out_code)
            self.assertEqual(
                product['allowSellingWithoutStock'],
                product_data['allowSellingWithoutStock']
            )
            self.assertEqual(
                product['manageSerial'],
                product_data['manageSerial']
            )
            self.assertEqual(
                product['autoGenerateSerial'],
                product_data['autoGenerateSerial']
            )
            self.assertEqual(
                product['expiryTracking'],
                product_data['expiryTracking']
            )
            self.assertEqual(
                product['expirationType'],
                product_data['expirationType']
            )
            self.assertEqual(
                product['daysBeforeExpLock'],
                product_data['daysBeforeExpLock']
            )

    def test_passValidData__returnCreateSuccess(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)
            self.assertEqual('processing', self.product.editing_status_code)
            self.assert_sellable_products(body['result'])

    def test__passSKUWithMoreThan20Char__returnInvalidRequest(self):
        self.sellable_products_data[0]['sku'] = fake.text(length=30)
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passSKUWithSpecialCharacters__returnInvalidRequest(self):
        self.sellable_products_data[0]['sku'] = '㠰毥崯'
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passBarcodeWithMoreThan30Char__returnInvalidRequest(self):
        self.sellable_products_data[0]['barcode'] = fake.text(length=50)
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passBarcodeWithSpecialCharacters__returnInvalidRequest(self):
        self.sellable_products_data[0]['barcode'] = '㠰毥崯'
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passPriceNotInteger__returnInvalidRequest(self):
        self.sellable_products_data[0]['supplierSalePrice'] = '10000000'
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passPriceMoreThan10Digits__returnInvalidRequest(self):
        self.sellable_products_data[0]['supplierSalePrice'] = 9999999999 + 1
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passNegativePrice__returnInvalidRequest(self):
        self.sellable_products_data[0]['supplierSalePrice'] = -1
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passAllowSellingWithoutStockNotBoolean__returnInvalidRequest(self):
        self.sellable_products_data[0]['allowSellingWithoutStock'] = 69
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_notPassAllowSellingWithoutStock__returnSuccessRequest(self):
        del self.sellable_products_data[0]['allowSellingWithoutStock']
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code)

    def test_passManageSerialTypeNotBoolean__returnInvalidRequest(self):
        self.sellable_products_data[0]['manageSerial'] = 69
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_notPassManageSerial__returnInvalidRequest(self):
        del self.sellable_products_data[0]['manageSerial']
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passAutoGenerateSerialNotBoolean__returnInvalidRequest(self):
        self.sellable_products_data[0]['autoGenerateSerial'] = 69
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_notManageSerialAndAutoGenerateSerial__returnInvalidRequest(self):
        self.sellable_products_data[0]['manageSerial'] = False
        self.sellable_products_data[0]['autoGenerateSerial'] = True
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_ExpiryTrackingAndNotManageExpiry__returnInvalidRequest(self):
        self.sellable_products_data[0]['expiryTracking'] = True
        self.sellable_products_data[0].pop('expirationType')
        self.sellable_products_data[0].pop('daysBeforeExpLock')
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(400, code)

    def test_passProviderInvalidSeller__raiseBadRequestException(self):
        with patch('catalog.services.provider.get_provider_by_id') as mock_get_provider:
            self.sellable_products_data[0]['providerId'] = fake.integer() + 1
            mock_get_provider.return_value = {
                'sellerID': 2,
                'isActive': 1
            }
            with logged_in_user(self.user):
                code, body = self.call_api(data=self.data)
                self.assertEqual(400, code)

    def test_passProviderInvalidNotFao__raiseBadRequestException(self):
        self.sellable_products_data[0]['providerId'] = fake.integer() + 1
        with patch('catalog.services.provider.get_provider_by_id') as mock_get_provider:
            mock_get_provider.return_value = None
            with logged_in_user(self.user):
                code, body = self.call_api(data=self.data)
                self.assertEqual(400, code)

    def test_400_shippingTypeIsNotExist(self):
        self.sellable_products_data[0]['shippingTypes'] = [self.shipping_types[0].id, 123]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

    def test_200_shippingTypeIsAnEmptyList(self):
        self.sellable_products_data[0]['shippingTypes'] = []

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

    def test_200_missingShippingType(self):
        del self.sellable_products_data[0]['shippingTypes']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

    def test_200_ShippingTypesFieldIsNull(self):
        self.sellable_products_data[0]['shippingTypes'] = None

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

    def test_400_shippingTypeIsInactive(self):
        inactive_shipping_type = fake.shipping_type(is_active=0)
        self.sellable_products_data[0]['shippingTypes'] = [self.shipping_types[0].id, inactive_shipping_type.id]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')


class TestCreateProductWithFBSSeller(CreateSellableProductTestCase):
    ISSUE_KEY = 'CATALOGUE-448'
    FOLDER = '/Sellable/Create'

    def testCreateWithSellerFillBySeller(self):
        with patch('catalog.services.seller.get_seller_by_id') as mock_seller:
            mock_seller.return_value = {
                'id': 1,
                'servicePackage': 'FBS'
            }
            with logged_in_user(self.user):
                code, body = self.call_api(data=self.data)
                self.assertEqual(200, code)
                product = random.choice(body.get('result'))  # type: dict
                self.assertNotEquals(product.get('sellingStatus', {}), 'hang_ban')

    def testCreateWithSellerNotFillBySeller(self):
        with patch('catalog.services.seller.get_seller_by_id') as mock_seller:
            mock_seller.return_value = {
                'id': 1,
                'servicePackage': fake.text()
            }
            with logged_in_user(self.user):
                code, body = self.call_api(data=self.data)
                product = random.choice(body.get('result'))  # type: dict
                self.assertNotEquals(product.get('sellingStatus'), 'hang_ban')


class CreateSellableProductWithDefaultShippingTypeTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-700'
    FOLDER = '/Sellable/CreateSellableProductWithDefaultShippingType'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller(manual_sku=True, is_manage_price=True)
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.variants = [fake.product_variant(product_id=self.product.id)
                         for _ in range(3)]
        [fake.shipping_type() for _ in range(5)]
        self.shipping_type_default = fake.shipping_type(is_default=1)
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
            'daysBeforeExpLock': random.randint(1, 10000)
        } for i in range(3)]
        for data in self.sellable_products_data:
            data['autoGenerateSerial'] = False if not data['manageSerial'] \
                else random.choice([True, False])
        self.data = {
            'productId': self.product.id,
            'sellableProducts': self.sellable_products_data
        }

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'POST'

    def assert_default_shipping_type(self, body):
        sellable_products = body['result']
        self.assertEqual(len(sellable_products), 3)
        for sellable_product in sellable_products:
            sellable_shipping_types = models.SellableProductShippingType.query.filter(
                models.SellableProductShippingType.sellable_product_id == sellable_product['id']
            ).all()
            self.assertEqual(len(sellable_shipping_types), 1)
            sellable_shipping_type = sellable_shipping_types[0]
            self.assertEqual(sellable_shipping_type.shipping_type_id, self.shipping_type_default.id)

    def test_200_create_without_shipping_type(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)
            self.assertEqual('processing', self.product.editing_status_code)

            self.assert_default_shipping_type(body)

    def test_200_create_with_shipping_type_is_empty_in_param(self):
        with logged_in_user(self.user):
            for data in self.data['sellableProducts']:
                data['shippingTypes'] = []
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)
            self.assertEqual('processing', self.product.editing_status_code)

            self.assert_default_shipping_type(body)
