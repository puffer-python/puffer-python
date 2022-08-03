# coding=utf-8

import random
from mock import patch

from tests.catalog.api import APITestCase
from tests.utils import JiraTest
from tests import logged_in_user
from tests.faker import fake
from catalog import utils
from catalog.services.products.sellable import (
    create_sellable_products,
    update_common
)
from catalog import models


class SyncSellableToSrm(APITestCase, JiraTest):
    ISSUE_KEY = 'SC-546'

    def setUp(self):
        self.user = fake.iam_user()
        self.product = fake.product()
        self.variants = [fake.product_variant(product_id=self.product.id)
                         for _ in range(3)]

    def test_syncSellable__whenCreateSellable(self):
        price = fake.integer(max=1000000000)
        self.sellable_products_data = [{
            'variant_id': self.variants[i].id,
            'sku': utils.random_string(12),
            'barcode': utils.random_string(10),
            'supplier_sale_price': price,
            'part_number': fake.text(),
            'allow_selling_without_stock': random.choice([True, False]),
            'manage_serial': random.choice([True, False]),
            'expiry_tracking': random.choice([True, False]),
            'expiration_type': random.choice([1, 2]),
            'days_before_exp_lock': random.randint(1, 10000)
        } for i in range(3)]
        for data in self.sellable_products_data:
            data['auto_generate_serial'] = False if not data['manage_serial'] \
                else random.choice([True, False])
        self.data = {
            'product_id': self.product.id,
            'sellable_products': self.sellable_products_data
        }

        with logged_in_user(self.user):
            with patch('catalog.extensions.signals.sellable_create_signal.send') as mock_create_signal:
                create_sellable_products(self.data)
                sellables = models.SellableProduct.query.all()
                for item in sellables:
                    mock_create_signal.assert_called()

    def test_syncSellable__whenUpdateCommonInfo(self):
        sellable = fake.sellable_product()
        data = {
            'name': fake.name(),
            'created_by': fake.text(),
        }
        with patch('catalog.extensions.signals.sellable_update_signal.send') as mock_update_signal:
            update_common(sku_id=sellable.id, data=data)
            mock_update_signal.assert_called_once_with(sellable)

    def test_syncSellable__whenUpdateEditingStatusToActive(self):
        sellables = [fake.sellable_product(
            variant_id=self.variants[0].id,
            editing_status_code='pending_approval'
        ) for _ in range(2)]
        ids = list(map(lambda x: x.id, sellables))

    def test_syncSellable__whenUpdateEditingStatusToInactive(self):
        sellables = [fake.sellable_product(
            variant_id=self.variants[0].id,
            editing_status_code='active'
        ) for _ in range(2)]
        ids = list(map(lambda x: x.id, sellables))

    def test_syncSellable__whenUpdateEditingStatusReject(self):
        sellables = [fake.sellable_product(
            variant_id=self.variants[0].id,
            editing_status_code='pending_approval'
        ) for _ in range(2)]
        ids = list(map(lambda x: x.id, sellables))
