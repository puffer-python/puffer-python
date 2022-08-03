# coding=utf-8
# pylint: disable=E0401
from abc import ABC

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestCreateSubSKU(APITestCase, ABC):
    ISSUE_KEY = 'CATALOGUE-1112'
    FOLDER = '/Sku/UpdateSku/SubSKU'

    def url(self):
        return f'/skus/{self.sku.sku}/child'

    def method(self):
        return 'POST'

    def setUp(self):
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by='dungbv')
        self.variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        self.sku = fake.sellable_product(variant_id=self.variant.id, barcode=fake.text(20),
                                         seller_id=self.category.seller_id)
        self.iam_user = fake.iam_user(seller_id=self.category.seller_id)

    def call_api(self, **kwargs):
        with logged_in_user(self.iam_user):
            return super().call_api(**kwargs)

    def testCreateSubSKU_success_return200(self):
        code, body = self.call_api(data={'sellerId': self.iam_user.seller_id})
        self.assertEqual(200, code)
        from catalog.models.sellable_product_sub_sku import SellableProductSubSku
        sub_sku = SellableProductSubSku.query.filter(SellableProductSubSku.sellable_product_id == self.sku.id).first()
        self.assertIsNotNone(sub_sku)

    def testCreateSubSKU_success_checkSKU_return200(self):
        self.call_api(data={'sellerId': self.iam_user.seller_id})
        code, body = self.call_api()
        self.assertEqual(200, code)
        self.assertEqual(body.get('result').get('sku')[-2:], '_2')

    def testCreateSubSKU_SKU_has10SubSKU_return400(self):
        for _ in range(10):
            self.call_api(data={'sellerId': self.iam_user.seller_id})
        code, body = self.call_api(data={'sellerId': self.iam_user.seller_id})
        self.assertEqual(400, code)
        self.assertEqual(body.get('message'), 'Sản phẩm đã có 10 sản phẩm con')
