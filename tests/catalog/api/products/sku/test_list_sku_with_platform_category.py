# coding=utf-8

import random

from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake


@patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
@patch('catalog.services.products.sku.get_platform_owner')
class TestListSKU(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1455'
    FOLDER = '/Sku/ListSkus/SearchByPlatformCategories'

    def url(self):
        return '/skus'

    def method(self):
        return 'GET'

    def generate_url(self, **kwargs):
        url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}'
        for key, value in kwargs.items():
            if key not in ("page", "pageSize"):
                url += f'&{key}={value}'
        return url

    def setUp(self):
        fake.init_editing_status()
        self.seller1 = fake.seller()
        self.seller2 = fake.seller()
        category = fake.category(seller_id=self.seller1.id)
        barcode = fake.text(25)
        self.sku = fake.sellable_product(
            barcode=barcode,
            seller_id=self.seller1.id
        )
        fake.product_category(
            product_id=self.sku.product_id,
            category_id=category.id,
            created_by='quanglm'
        )
        fake.sellable_product_barcode(sku_id=self.sku.id, barcode=barcode)
        fake.sellable_product_shipping_type(sellable_product_id=self.sku.id)
        fake.product_variant_images(variant_id=self.sku.variant_id)
        self.categories = [category]
        for i in range(10):
            category = fake.category(seller_id=self.seller1.id)
            self.categories.append(category)
            fake.product_category(
                product_id=self.sku.product_id,
                category_id=category.id,
                created_by='quanglm'
            )

    def test_list_sku_by_categories_return200_no_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = self.seller2.id
        mock_default_platform_owner.return_value = self.seller1.id
        url = self.generate_url(
            categoryIds=fake.category().id,
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_list_sku_by_categories_return200_only_one_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = self.seller2.id
        mock_default_platform_owner.return_value = self.seller1.id
        url = self.generate_url(
            categoryIds=f'{fake.category().id},{self.categories[random.randint(0, 10)].id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1

    @patch('catalog.services.seller.get_default_platform_owner_of_seller')
    def test_list_sku_by_categories_return200_only_one_sku_by_platform_category(self, mock_seller_default_owner_id,
                                                                                mock_platform_owner,
                                                                                mock_default_platform_owner):
        mock_seller_default_owner_id.return_value = self.seller2.id
        mock_platform_owner.return_value = self.seller2.id
        mock_default_platform_owner.return_value = self.seller1.id
        cat = self.categories[random.randint(0, 10)]
        platform_cat = fake.category(seller_id=self.seller2.id)
        total_new_sku = random.randint(5, 10)
        for i in range(total_new_sku):
            new_sku = fake.sellable_product(seller_id=self.seller1.id)
            fake.product_category(
                product_id=new_sku.product_id,
                category_id=cat.id,
                created_by='quanglm'
            )
            if i == 0:
                fake.product_category(
                    product_id=new_sku.product_id,
                    category_id=platform_cat.id,
                    created_by='quanglm'
                )

        url = self.generate_url(
            categoryIds=f'{platform_cat.id},{cat.id}',
            sellerIds=self.seller1.id
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1


    def test_list_sku_by_categories_return200_multiple_skus(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = self.seller2.id
        mock_default_platform_owner.return_value = self.seller1.id
        cat = self.categories[random.randint(0, 10)]
        total_new_sku = random.randint(1, 10)
        for _ in range(total_new_sku):
            new_sku = fake.sellable_product()
            fake.product_category(
                product_id=new_sku.product_id,
                category_id=cat.id,
                created_by='quanglm'
            )
        url = self.generate_url(
            categoryIds=f'{fake.category(seller_id=self.seller1.id).id},{cat.id}'
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == total_new_sku + 1
