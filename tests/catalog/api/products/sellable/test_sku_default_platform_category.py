# coding=utf-8
from catalog.biz.sellable import SellableCreateSchema
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import models as m


class TestCreateListSKuLayerSKU(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1344'
    FOLDER = '/Sku/GetSku/GetDefaultCategory'

    def test_get_seller_category_code_with_has_value(self):
        fake.platform_sellers(seller_id=1, platform_id=1, is_default=True, is_owner=True)
        fake.platform_sellers(seller_id=2, platform_id=1, is_default=True, is_owner=False)
        cat = fake.category(seller_id=1)
        sku = fake.sellable_product(seller_id=2)
        fake.product_category(
            product_id=sku.product_id,
            category_id=cat.id,
            created_by='quanglm'
        )
        sku.set_seller_category_code(m.db.session)
        data = SellableCreateSchema().dump(sku)
        self.assertEqual(cat.code, sku.seller_category_code)
        self.assertEqual(cat.code, data.get('categCode'))

    def test_get_seller_category_code_with_no_value(self):
        fake.platform_sellers(seller_id=1, platform_id=1, is_default=True, is_owner=True)
        fake.platform_sellers(seller_id=2, platform_id=1, is_default=True, is_owner=False)
        fake.platform_sellers(seller_id=3, platform_id=2, is_default=True, is_owner=True)
        fake.platform_sellers(seller_id=2, platform_id=2, is_default=False, is_owner=False)
        cat = fake.category(seller_id=3)
        sku = fake.sellable_product(seller_id=2)
        fake.product_category(
            product_id=sku.product_id,
            category_id=cat.id,
            created_by='quanglm'
        )
        sku.set_seller_category_code(m.db.session)
        self.assertEqual('', sku.seller_category_code)
