# coding=utf-8

import pytest

from catalog import models
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators.sellable import UpdateEditingStatusValidator
from catalog.api.product.sellable.schema import UpdateEditingStatusRequestBody


class UpdateEditingStatusTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-901'
    FOLDER = '/Sellable/EditingStatus/Update'

    def url(self):
        return '/sellable_products/status'

    def method(self):
        return 'PATCH'

    def setUp(self):
        fake.init_editing_status()
        self.attribute_set = fake.attribute_set()
        self.attribute_group = fake.attribute_group(self.attribute_set.id)
        self.user = fake.iam_user()
        self.product = fake.product(
            editing_status_code='processing',
            attribute_set_id=self.attribute_set.id,
        )

    def fake_skus(self, len_skus=1, fake_image=True, **kwargs):
        self.skus = []
        for index in range(len_skus):
            self.variant = fake.product_variant(
                product_id=self.product.id,
                editing_status_code='processing'
            )
            self.required_attr = fake.attribute(
                variant_id=self.variant.id,
                group_ids=[self.attribute_group.id],
                is_required=1
            )
            fake.attribute(
                variant_id=self.variant.id,
                group_ids=[self.attribute_group.id],
                is_required=0
            )
            if fake_image:
                self.image = fake.variant_product_image(self.variant.id)

            sellable = fake.sellable_product(
                variant_id=self.variant.id,
                editing_status_code=kwargs.get('editing_status'),
                seller_id=self.user.seller_id,
                description=fake.text(),
                detailed_description=kwargs.get('detailed_description', None),
                attribute_set_id=self.attribute_set.id,
            )
            self.skus.append(sellable)

    def test_200_passValidIds(self):
        self.fake_skus(len_skus=2, editing_status='processing')
        self.data = {
            'ids': [sku.id for sku in self.skus],
            'status': 'pending_approval'
        }
        code, body = self.call_api_with_login(self.data)
        self.assertEqual(code, 200, body)
        for sku in self.skus:
            sellable = models.SellableProduct.query.get(sku.id)
            self.assertEqual(sellable.editing_status_code, 'pending_approval')
        ids = body['result']['ids']
        self.assertEqual(len(ids), 2)
        for id in ids:
            self.assertIn(id, [sku.id for sku in self.skus])
        skus = body['result']['skus']
        self.assertEqual(len(skus), 2)
        for sku in skus:
            self.assertIn(sku, [sku.sku for sku in self.skus])

    def test_200_passValidSkus(self):
        self.fake_skus(len_skus=2, editing_status='processing')
        self.data = {
            'skus': [sku.sku for sku in self.skus],
            'status': 'pending_approval'
        }
        code, body = self.call_api_with_login(self.data)
        self.assertEqual(code, 200, body)
        for sku in self.skus:
            sellable = models.SellableProduct.query.filter_by(
                sku=sku.sku
            ).first()
            self.assertEqual(sellable.editing_status_code, 'pending_approval')
        ids = body['result']['ids']
        self.assertEqual(len(ids), 2)
        for id in ids:
            self.assertIn(id, [sku.id for sku in self.skus])
        skus = body['result']['skus']
        self.assertEqual(len(skus), 2)
        for sku in skus:
            self.assertIn(sku, [sku.sku for sku in self.skus])

    def test_400_sellableWithoutDetailedDescription(self):
        self.fake_skus(len_skus=1, editing_status='processing', detailed_description=None)
        self.data = {
            'skus': [sku.sku for sku in self.skus],
            'status': 'pending_approval'
        }
        self.skus[0].terminal_seo.description = ''
        models.db.session.commit()
        code, body = self.call_api_with_login(self.data)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['message'], f'Sản phẩm {self.skus[0].name} thiếu mô tả đặc điểm chi tiết')

    def test_400_passSellableWithoutImage(self):
        self.fake_skus(len_skus=1, fake_image=False, editing_status='processing', detailed_description='')
        self.data = {
            'skus': [sku.sku for sku in self.skus],
            'status': 'pending_approval'
        }
        code, body = self.call_api_with_login(self.data)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['message'], f'Sản phẩm {self.skus[0].name} cần có ít nhất 1 hình ảnh')

    def test_400_mustExistIdsOrSkus(self):
        self.fake_skus(len_skus=1, fake_image=False, editing_status='processing', detailed_description=None)
        self.data = {
            'status': 'pending_approval'
        }
        code, body = self.call_api_with_login(self.data)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['message'], 'Phải tồn tại ít nhất một sellable')
