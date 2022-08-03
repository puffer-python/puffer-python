# coding=utf-8
import io
import math

import pandas
from sqlalchemy import and_

from catalog import models
from catalog.utils.lambda_list import LambdaList
from tests import logged_in_user
from tests.catalog import ATTRIBUTE_TYPE
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetUpdateProductAttributeTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-643'
    FOLDER = '/Import/GetUpdateProductAttributeTemplate'

    def url(self):
        url = '/import?type=update_attribute_product'
        if self.attribute_set_id:
            url += f'&attributeSetId={self.attribute_set_id}'
        return url

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

    def tearDown(self):
        pass

    def test_return200__Fail_InvalidAttributeSetId(self):
        self.attribute_set_id = 1
        code, body = self.call_api_with_login()
        self.assertEqual(400, code)
        self.assertEqual('Bộ thuộc tính không tồn tại', body['message'])

    def test_return200__Fail_MissingAttributeSetId(self):
        self.attribute_set_id = None
        code, body = self.call_api_with_login()
        self.assertEqual(400, code)
        self.assertEqual('Bộ thuộc tính không tồn tại', body['message'])

    def test_return200__Success_Matching_File(self):
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [fake.attribute_group(set_id=self.attribute_set.id) for _ in range(3)]
        self.attributes = [fake.attribute(code=f'attribute_{i}') for i in range(20)]
        self.uom_attribute = fake.uom_attribute(self.attribute_set.id)
        self.uom_ratio_attribute = fake.uom_ratio_attribute(self.attribute_set.id)

        attribute_group_ids = LambdaList(self.attribute_groups).map(lambda x: x.id).list()
        for item in self.attributes:
            fake.attribute_group_attribute(item.id, attribute_group_ids)

        self.attribute_set_id = self.attribute_set.id
        code, body = self.call_api_with_login()
        sheet_san_pham = pandas.read_excel(io.BytesIO(body), header=5, dtype=str, sheet_name='Update_SanPham')
        self.assertEqual(code, 200)

        # general info header
        general_info_columns = ["seller_sku", "unit of measure", "uom ratio"]
        self.assertListEqual(LambdaList(sheet_san_pham.columns).take(len(general_info_columns)).list(),
                             general_info_columns,
                             'Match general info column header')

        # attribute header
        attribute_groups = models.AttributeGroup.query.filter(
            and_(
                models.AttributeGroup.attribute_set_id == self.attribute_set.id
            )
        ).order_by(models.AttributeGroup.priority).all()

        attribute_headers = []
        for attribute_group in attribute_groups:
            attribute_group_attributes = models.AttributeGroupAttribute.query \
                .filter(models.AttributeGroupAttribute.attribute_group_id == attribute_group.id) \
                .order_by(models.AttributeGroupAttribute.priority) \
                .all()
            for attribute_group_attribute in attribute_group_attributes:
                if attribute_group_attribute.attribute.code not in ['uom', 'uom_ratio']:
                    attribute_headers.append(models.Attribute.query.get(attribute_group_attribute.attribute_id))

        in_file_attribute_headers = LambdaList(sheet_san_pham.columns).skip(len(general_info_columns)).list()
        in_db_attribute_headers = LambdaList(attribute_headers).map(lambda x: x.code).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers')

        has_option_attributes = LambdaList(attribute_headers).filter(
            lambda x: x.value_type in (ATTRIBUTE_TYPE.SELECTION, ATTRIBUTE_TYPE.MULTIPLE_SELECT)).list()

        sheet_du_lieu_mau = pandas.read_excel(io.BytesIO(body), header=0, dtype=str, sheet_name='DuLieuMau')
        in_file_attribute_headers = LambdaList(sheet_du_lieu_mau.columns).list()
        in_db_attribute_headers = LambdaList(has_option_attributes).map(lambda x: x.display_name).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers for DuLieuMau sheet')

        for attribute in has_option_attributes:
            in_file_values = LambdaList(
                sheet_du_lieu_mau[attribute.display_name]
            ).filter(lambda x: x and (x == x)).list()
            in_db_values = LambdaList(attribute.options).map(lambda x: x.value).list()
            self.assertListEqual(in_file_values,
                                 in_db_values,
                                 'Match attribute value for DuLieuMau sheet')


class GetUpdateProductAttributeDisplayNameTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1098'
    FOLDER = '/Import/GetUpdateProductAttributeTemplate/Attribute/Display'

    def url(self, create=False):
        url = '/import?type=update_attribute_product'
        if create:
            url = '/import?type=create_product'
        if self.attribute_set_id:
            url += f'&attributeSetId={self.attribute_set_id}'
        return url

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [fake.attribute_group(set_id=self.attribute_set.id) for _ in range(3)]
        self.attributes = [fake.attribute(code=f'attribute_{i}') for i in range(20)]
        self.uom_attribute = fake.uom_attribute(self.attribute_set.id)
        self.uom_ratio_attribute = fake.uom_ratio_attribute(self.attribute_set.id)

        attribute_group_ids = LambdaList(self.attribute_groups).map(lambda x: x.id).list()
        for item in self.attributes:
            fake.attribute_group_attribute(item.id, attribute_group_ids)

        self.attribute_set_id = self.attribute_set.id

    def test_get_update_product_attribute_template_return200__Success_Matching_File(self):
        code, body = self.call_api_with_login()
        self.assertEqual(code, 200)

        # attribute header
        general_info_columns = ["seller_sku", "unit of measure", "uom ratio"]
        attribute_groups = models.AttributeGroup.query.filter(
            and_(
                models.AttributeGroup.attribute_set_id == self.attribute_set.id
            )
        ).order_by(models.AttributeGroup.priority).all()

        attribute_headers = []
        for attribute_group in attribute_groups:
            attribute_group_attributes = models.AttributeGroupAttribute.query \
                .filter(models.AttributeGroupAttribute.attribute_group_id == attribute_group.id) \
                .order_by(models.AttributeGroupAttribute.priority) \
                .all()
            for attribute_group_attribute in attribute_group_attributes:
                if attribute_group_attribute.attribute.code not in ['uom', 'uom_ratio']:
                    attribute_headers.append(models.Attribute.query.get(attribute_group_attribute.attribute_id))

        sheet_san_pham = pandas.read_excel(io.BytesIO(body), header=5, dtype=str, sheet_name='Update_SanPham')
        in_file_attribute_headers = LambdaList(sheet_san_pham.columns).skip(len(general_info_columns)).list()
        in_db_attribute_headers = LambdaList(attribute_headers).map(lambda x: x.code).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers')

        has_option_attributes = LambdaList(attribute_headers).filter(
            lambda x: x.value_type in (ATTRIBUTE_TYPE.SELECTION, ATTRIBUTE_TYPE.MULTIPLE_SELECT)).list()
        sheet_du_lieu_mau = pandas.read_excel(io.BytesIO(body), header=0, dtype=str, sheet_name='DuLieuMau')
        in_file_attribute_headers = LambdaList(sheet_du_lieu_mau.columns).list()
        in_db_attribute_headers = LambdaList(has_option_attributes).map(lambda x: x.display_name).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers for DuLieuMau sheet')

    def test_get_create_product_template_return200__Success_Matching_File(self):
        code, body = self.call_api_with_login(url=self.url(create=True))
        self.assertEqual(code, 200)

        # attribute header
        general_info_columns = ['type', 'master category', 'category', 'product name', 'brand', 'model',
                                'warranty months', 'warranty note', 'vendor tax', 'product type',
                                'short description', 'description']
        sample_info_columns = ['Loại sản phẩm', 'Danh mục ngành hàng', 'Danh mục', 'Thương hiệu', 'Đơn vị tính',
                                'Loại hình sản phẩm', 'Thuế suất', 'Loại hình vận chuyển']
        attribute_groups = models.AttributeGroup.query.filter(
            and_(
                models.AttributeGroup.attribute_set_id == self.attribute_set.id
            )
        ).order_by(models.AttributeGroup.priority).all()

        attribute_headers = []
        for attribute_group in attribute_groups:
            attribute_group_attributes = models.AttributeGroupAttribute.query \
                .filter(models.AttributeGroupAttribute.attribute_group_id == attribute_group.id) \
                .order_by(models.AttributeGroupAttribute.priority) \
                .all()
            for attribute_group_attribute in attribute_group_attributes:
                if attribute_group_attribute.attribute.code not in ['uom', 'uom_ratio']:
                    attribute_headers.append(models.Attribute.query.get(attribute_group_attribute.attribute_id))

        sheet_san_pham = pandas.read_excel(io.BytesIO(body), header=5, dtype=str, sheet_name='Import_SanPham')
        in_db_attribute_headers = LambdaList(attribute_headers).map(lambda x: x.code).list()
        in_file_attribute_headers = LambdaList(sheet_san_pham.columns).skip(len(general_info_columns)).take(
            len(in_db_attribute_headers)).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers')

        has_option_attributes = LambdaList(attribute_headers).filter(
            lambda x: x.value_type in (ATTRIBUTE_TYPE.SELECTION, ATTRIBUTE_TYPE.MULTIPLE_SELECT)).list()
        sheet_du_lieu_mau = pandas.read_excel(io.BytesIO(body), header=0, dtype=str, sheet_name='DuLieuMau')
        in_file_attribute_headers = LambdaList(sheet_du_lieu_mau.columns).skip(len(sample_info_columns)).list()
        in_db_attribute_headers = LambdaList(has_option_attributes).map(lambda x: x.display_name).list()
        self.assertListEqual(in_file_attribute_headers,
                             in_db_attribute_headers,
                             'Match attribute headers for DuLieuMau sheet')
