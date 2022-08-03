# coding=utf-8
import io
import random
import string
from abc import ABCMeta

import pandas as pd
import pytest
from sqlalchemy import text, and_

from catalog.models import db
from catalog.services.products.sellable import _safe_get_value
from catalog.utils.lambda_list import LambdaList
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake
from tests import logged_in_user
from catalog import models


class ExportListSellableProductDetailTestCase(APITestCaseWithMysql, metaclass=ABCMeta):
    ISSUE_KEY = 'CATALOGUE-528'
    FOLDER = '/Product/ExportListSellableProductDetail'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        self.category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [fake.attribute_group(set_id=self.attribute_set.id) for _ in range(3)]
        self.attributes = [fake.attribute() for _ in range(20)]

        attribute_group_id = LambdaList(self.attribute_groups).map(lambda x: x.id).list()
        for item in self.attributes:
            fake.attribute_group_attribute(item.id, attribute_group_id)

        self.uom_attribute = fake.uom_attribute(self.attribute_set.id)
        # self.attributes.append(self.uom_attribute)

        self.skus = [fake.sellable_product(category_id=self.category.id, seller_id=self.seller.id,
                                           attribute_set_id=self.attribute_set.id)
                     for _ in range(10)]

        for sku in self.skus:
            for attribute in self.attributes:
                if attribute.value_type == 'text' or attribute.value_type == 'number':
                    fake.variant_attribute(variant_id=sku.variant_id, attribute_id=attribute.id)
                elif attribute.value_type == 'selection':
                    all_options = models.AttributeOption.query.filter(
                        models.AttributeOption.attribute_id == attribute.id).all()
                    fake.variant_attribute(variant_id=sku.variant_id, attribute_id=attribute.id,
                                           option_id=random.choice(all_options).id)
                elif attribute.value_type == 'multiple_select':
                    all_options = models.AttributeOption.query.filter(
                        models.AttributeOption.attribute_id == attribute.id).all()
                    options = LambdaList(random.sample(all_options, 2)).map(lambda x: x.id).string_join(",")
                    fake.variant_attribute(variant_id=sku.variant_id, attribute_id=attribute.id,
                                           value=options)

    def tearDown(self):
        pass

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'GET'

    def get_data(self, data=None, content_type=None, method=None, url=None):
        url = f'{url}&export=2'
        code, body = self.call_api_with_login(data, content_type, method, url)
        return code, body

    def assertEqualStr(self, value1, value2, message=None):
        filter_value1 = '' if value1 is None or str(value1) == 'nan' else str(value1)
        filter_value2 = '' if value2 is None or str(value2) == 'nan' else str(value2)
        self.assertEqual(filter_value1, filter_value2, message)

    def test_return400__MissingAttributeSetIdParam(self):
        url = f'{self.url()}?page=1'
        code, body = self.get_data(url=url)
        self.assertEqual(400, code, 'StatusCode = 400')
        self.assertEqual(body.get('message'), 'missing attribute_set param')

    def test_return400__MultiAttributeSetIdParam(self):
        url = f'{self.url()}?attributeSet=1,2,3,4'
        code, body = self.get_data(url=url)
        self.assertEqual(400, code, 'StatusCode = 400')
        self.assertEqual(body.get('message'), 'only 1 attribute_set_id is allow at attribute_set param')

    def test_return200__Success(self):
        url = f'{self.url()}?attributeSet={self.attribute_set.id}'
        code, body = self.get_data(url=url)
        self.assertEqual(200, code, 'StatusCode = 200')
