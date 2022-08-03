# coding=utf-8
import io
import random

import pandas

from catalog.services.imports.template import TemplateUpsertProductCategory
from catalog.utils.lambda_list import LambdaList
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestGetUpsertProductCategoryTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1129'
    FOLDER = '/Import/GetUpsertProductCategoryTemplate'

    def url(self):
        return '/import?type=upsert_product_category&platform_id=1'

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
                categories.append(f'{leaf_cat.id}=>{leaf_cat.full_path}')
        self.categories = categories

    def _get_categories_from_template(self, body):
        sheet_category = pandas.read_excel(io.BytesIO(body), header=0, dtype=str,
                                           sheet_name=TemplateUpsertProductCategory.TAB_FOR_SAMPLE_DATA)
        return sheet_category

    def test_export_template_return200_with_correct_data_categories(self):
        code, body = self.call_api_with_login()
        template_categories = self._get_categories_from_template(body)
        template_categories = LambdaList(template_categories['Danh mục ngành hàng']).filter(lambda x: x and (x == x)).list()
        self.assertListEqual(self.categories, template_categories)
