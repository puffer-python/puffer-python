# coding=utf-8

from mock import patch

from catalog.services.tax import TaxService
from tests.faker import fake
from tests.catalog.api import APITestCase

service = TaxService.get_instance()


class GetTaxesListTestCase(APITestCase):
    ISSUE_KEY = 'SC-385'

    def setUp(self):
        self.taxes = [fake.tax() for _ in range(3)]

    def url(self):
        return '/taxes'

    def method(self):
        return 'GET'

    @patch('catalog.services.tax.TaxService.get_taxes_list')
    def test_getAllTaxesList__returnListTax(self, mock):
        mock.return_value = self.taxes
        code, body = self.call_api()

        assert code, 200
        assert len(body['result']) == len(self.taxes)
        self.taxes = sorted(self.taxes, key=lambda tax: tax.code)
        ret = sorted(body['result'], key=lambda item: item['code'])
        for tax, real_tax in zip(self.taxes, ret):
            assert tax.code == real_tax['code']
            assert tax.amount == real_tax['amount']
            assert tax.label == real_tax['label']
