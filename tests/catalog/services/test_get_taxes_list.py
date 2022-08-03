#coding=utf-8

from catalog.services.tax import TaxService
from tests.faker import fake
from tests.catalog.api import APITestCase


service = TaxService.get_instance()

class GetTaxesListTestCase(APITestCase):
    ISSUE_KEY = 'SC-385'

    def setUp(self):
        self.taxes = [fake.tax() for _ in range(3)]

    def test_getAllTaxesList__returnListTax(self):
        ret = service.get_taxes_list()
        assert len(ret) == len(self.taxes)

        self.taxes = sorted(self.taxes, key=lambda tax: tax.id)
        ret = sorted(ret, key=lambda tax: tax.id)
        for tax, real_tax in zip(self.taxes, ret):
            assert tax == real_tax
