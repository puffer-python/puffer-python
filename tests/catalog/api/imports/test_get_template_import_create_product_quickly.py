# coding=utf-8
import io
import random
from mock import patch

import pandas

from catalog.services.imports.template import TemplateCreateProductQuickly
from catalog.utils.lambda_list import LambdaList
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.constants import UOM_CODE_ATTRIBUTE


class TestGetCreateProductQuicklyTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1322'
    FOLDER = '/Import/GetCreateProductQuicklyTemplate'

    def url(self):
        return '/extra?types=import_types'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)
        fake.misc(name='Đăng tải nhanh sản phẩm', data_type='import_type', code='create_product_quickly')

    def test_export_template_return200(self):
        code, body = self.call_api_with_login()
        import_types = body['result']['importTypes']
        quickly_import = next(filter(lambda x: x['code'] == 'create_product_quickly' \
                                               and x['name'] == 'Đăng tải nhanh sản phẩm', import_types), None)

        self.assertEqual(200, code)
        self.assertIsNotNone(200, quickly_import)



class TestExportCreateProductQuicklyTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1325'
    FOLDER = '/Import/GetCreateProductQuicklyTemplate'

    def url(self):
        return '/import?type=create_product_quickly'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)
        fake.platform_sellers(platform_id=1, seller_id=self.seller.id, is_default=True,
                              is_owner=True)
        categories = []
        for _ in range(random.randrange(5, 10)):
            cat = fake.category(seller_id=self.seller.id)
            for _ in range(random.randrange(2, 20)):
                leaf_cat = fake.category(seller_id=self.seller.id, parent_id=cat.id)
                categories.append(f'{leaf_cat.code}=>{leaf_cat.name}')
        self.categories = categories
        brands = []
        for _ in range(random.randrange(5, 10)):
            brand = fake.brand()
            brands.append(brand)
        self.brands = sorted(list(map(lambda x: x.name, brands)))
        self.unit_attribute = fake.attribute(code=UOM_CODE_ATTRIBUTE)
        for _ in range(random.randrange(5, 10)):
            fake.attribute_option(attribute_id=self.unit_attribute.id)
        terminal_groups = []
        for _ in range(random.randrange(10, 20)):
            terminal_groups.append({
                "code": fake.text(),
                "name": fake.text()
            })
        self.terminal_groups = terminal_groups

    def _get_sample_data(self, body, title):
        sample = pandas.read_excel(io.BytesIO(body), header=0, dtype=str,
                                   sheet_name=TemplateCreateProductQuickly.TAB_FOR_SAMPLE_DATA)
        return LambdaList(sample[title]).filter(lambda x: x and (x == x)).list()

    @patch('catalog.services.terminal.get_terminal_groups')
    def test_export_template_return200_with_correct_categories(self, mock):
        mock.return_value = self.terminal_groups
        code, body = self.call_api_with_login()
        template_categories = self._get_sample_data(body, 'Danh mục ngành hàng')
        self.assertListEqual(self.categories, template_categories)

    @patch('catalog.services.terminal.get_terminal_groups')
    def test_export_template_return200_with_correct_brands(self, mock):
        mock.return_value = self.terminal_groups
        code, body = self.call_api_with_login()
        template_brands = self._get_sample_data(body, 'Thương hiệu')
        self.assertListEqual(self.brands, template_brands)

    @patch('catalog.services.terminal.get_terminal_groups')
    def test_export_template_return200_with_correct_units(self, mock):
        mock.return_value = self.terminal_groups
        code, body = self.call_api_with_login()
        template_units = self._get_sample_data(body, 'Đơn vị tính')
        units = list(map(lambda x: x.value, self.unit_attribute.select_options))
        self.assertListEqual(units, template_units)

    @patch('catalog.services.terminal.get_terminal_groups')
    def test_export_template_return200_with_correct_terminal_groups(self, mock):
        mock.return_value = self.terminal_groups
        code, body = self.call_api_with_login()
        template_groups = self._get_sample_data(body, 'Nhóm điểm bán')
        self.assertListEqual(list(map(lambda x: f'{x["code"]}=>{x["name"]}', self.terminal_groups)), template_groups)
