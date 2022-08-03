# coding=utf-8
# pylint: disable=E0401
from abc import ABC
from random import random

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestMoveGoupSKU(APITestCase, ABC):
    ISSUE_KEY = 'CATALOGUE-1178'
    FOLDER = '/Sku/UpdateSku/MoveGroup'

    def url(self):
        return f'/skus/{self.sku}/move-group'

    def method(self):
        return 'POST'

    def setUp(self):
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by='dungbv')
        self.variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        self.sellable_product = fake.sellable_product(variant_id=self.variant.id, barcode=fake.text(20),
                                                      seller_id=self.category.seller_id)
        self.iam_user = fake.iam_user(seller_id=self.category.seller_id)
        self.sku = self.sellable_product.sku

    def call_api(self, **kwargs):
        with logged_in_user(self.iam_user):
            return super().call_api(**kwargs)

    def testMoveGroupSKU_invalidSku_return400(self):
        code, body = self.call_api()
        self.assertEqual(400, code)

    def testMoveGroupSKU_return200(self):
        fake_sku = fake.sellable_product(
            variant_id=self.variant.id, barcode=fake.text(20),
            seller_id=self.category.seller_id)
        code, body = self.call_api(data={"sku": fake_sku.sku})
        self.assertEqual(200, code)

    def testMoveGroupSKU_invalidAttributeSet_return400(self):
        fake_sku = fake.sellable_product(
            variant_id=self.variant.id, barcode=fake.text(20),
            seller_id=self.category.seller_id)
        fake_sku.attribute_set_id = fake_sku.attribute_set_id + fake.id()
        code, body = self.call_api(data={"sku": fake_sku.sku})
        self.assertEqual(400, code)
        self.assertEqual(body.get("message"), "Chỉ có gom nhóm những sản phầm cùng Bộ thuộc tính")

    def testMoveGroupSKU_invalidAttributeVariant_return400(self):
        fake_sku = fake.sellable_product(
            variant_id=self.variant.id, barcode=fake.text(20),
            seller_id=self.category.seller_id)
        code, body = self.call_api(data={"sku": fake_sku.sku + fake.text()})
        self.assertEqual(400, code)
        self.assertEqual(body.get("message"), "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại")

    def testMoveGroupSKU_invalidBrandId_return400(self):
        fake_sku = fake.sellable_product(
            variant_id=self.variant.id, barcode=fake.text(20),
            seller_id=self.category.seller_id)
        fake_sku.brand_id = fake_sku.brand_id + fake.id()
        code, body = self.call_api(data={"sku": fake_sku.sku})
        self.assertEqual(400, code)
        self.assertEqual(body.get("message"), "Chỉ có gom nhóm những sản phầm cùng Thương hiệu")
