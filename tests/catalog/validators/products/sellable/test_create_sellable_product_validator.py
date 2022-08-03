# coding=utf-8
import logging
import random

import pytest

from catalog import utils
from tests import logged_in_user
from tests.catalog.validators import BaseValidatorTestCase
from tests.faker import fake
from catalog.extensions import exceptions as exc
from catalog.api.product.sellable import schema
from catalog.validators.sellable import CreateSellableProductsValidator
from tests.utils import JiraTest

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateSellableProductValidatorTestCase(BaseValidatorTestCase, JiraTest):
    # ISSUE_KEY = 'SC-536'
    ISSUE_KEY = 'SC-652'

    def setUp(self):
        super().setUp()
        self.product = fake.product()
        self.variants = [fake.product_variant(product_id=self.product.id)
                         for _ in range(3)]
        price = fake.integer(max=1000000000)
        self.seller = fake.seller(manual_sku=True, is_manage_price=False)
        self.sellable_products_data = [{
            'variantId': self.variants[i].id,
            'sku': utils.random_string(12),
            'barcode': utils.random_string(10),
            'supplierSalePrice': price,
            'partNumber': fake.text(),
            'allowSellingWithoutStock': random.choice([True, False]),
            'expiryTracking': random.choice([True, False]),
            'expirationType': random.choice([1, 2]),
            'daysBeforeExpLock': random.randint(1, 10000)
        } for i in range(3)]
        for product_data in self.sellable_products_data:
            product_data['manageSerial'] = random.choice([True, False])
            product_data['autoGenerateSerial'] = \
                False if not product_data['manageSerial'] \
                    else random.choice([True, False])
        self.data = {
            'productId': self.product.id,
            'sellableProducts': self.sellable_products_data
        }
        self.declare_schema(schema.SellableProductsRequest)
        self.invoke_validator(CreateSellableProductsValidator)

    def test_sellerNotManualSKU__raiseBadRequestException(self):
        self.seller.manual_sku = False
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_skuExisted__raiseBadRequestException(self):
        sellable = fake.sellable_product(seller_id=self.seller.id)
        self.sellable_products_data[0]['sku'] = sellable.sku
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_barcodeExisted__raiseBadRequestException(self):
        sellable = fake.sellable_product(seller_id=self.seller.id)
        self.sellable_products_data[0]['barcode'] = sellable.barcode
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passPriceWhileSellerUseOtherManagePriceModule__raiseBadRequestException(self):
        self.seller.is_manage_price = False
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passAutoGenerateSerialTrueWhileManageSerial__raiseBadRequestException(self):
        self.sellable_products_data[0]['manageSerial'] = False
        self.sellable_products_data[0]['autoGenerateSerial'] = True
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_ExpiryTrackingButNotManageExpiration__raiseBadRequestException(self):
        self.sellable_products_data[0]['expiryTracking'] = True
        self.sellable_products_data[0].pop('expirationType')
        self.sellable_products_data[0].pop('daysBeforeExpLock')
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passUnacceptedDataWhenProductIsBundle__raiseBadRequestException(self):
        self.product.is_bundle = True
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)
