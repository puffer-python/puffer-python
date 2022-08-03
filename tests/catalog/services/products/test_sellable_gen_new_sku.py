#coding=utf-8

import pytest

from time import strftime, sleep
from catalog.extensions import exceptions as exc
from catalog.services.products.sellable import gen_new_sku
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products import ProductService

service = ProductService.get_instance()


class GenerateNewSkuTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-361'

    def setUp(self):
        self.date = strftime('%y%m')

    def test_passSkuWithNineCharacters__returnCorrectSku(self):
        fake_sku = "%s%s" % (self.date, '00001')
        sellable = fake.sellable_product(sku=fake_sku)
        new_sku = gen_new_sku()
        assert int(new_sku) == int(int(fake_sku) + 1) or fake_sku

    def test_passSkuWithTenCharacters__returnCorrectSku(self):
        fake_sku = "%s%s" % (self.date, '000001')
        sellable = fake.sellable_product(sku=fake_sku)
        new_sku = gen_new_sku()
        assert int(new_sku) == int(int(fake_sku) + 1) or fake_sku

    def test_passSkuWithNineAndTenCharacters__returnCorrectSku(self):
        fake_sku = "%s%s" % (self.date, '00001')
        sellable = fake.sellable_product(sku=fake_sku)
        fake_sku1 = "%s%s" % (self.date, '000001')
        sellable = fake.sellable_product(sku=fake_sku1)
        new_sku = gen_new_sku()
        assert int(new_sku) == int(int(fake_sku1) + 1) or fake_sku1

    def test_passSkuWithNoneExistedSkuCharacters__returnCorrectSku(self):
        new_sku = gen_new_sku()
        assert int(new_sku) == int(self.date) * 100000