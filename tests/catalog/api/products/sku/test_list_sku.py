# coding=utf-8

import random

from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake

@patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
@patch('catalog.services.products.sku.get_platform_owner')
class TestListSKU(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1068'
    FOLDER = '/Sku/ListSkus/SearchByBarcodes'

    def url(self):
        return '/skus'

    def method(self):
        return 'GET'

    def generate_url(self, **kwargs):
        seller_ids = ','.join([str(sku.seller_id) for sku in self.skus])
        url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}' \
              f'&sellerIds={seller_ids}&platformId=1'
        for key, value in kwargs.items():
            if key not in ("page", "pageSize"):
                url += f'&{key}={value}'
        return url

    def setUp(self):
        fake.init_editing_status()
        self.skus = []
        for i in range(10):
            barcodes = [fake.text(25) for _ in range(2)]
            category = fake.category()
            sku = fake.sellable_product(
                barcode=barcodes[1],
                seller_id=category.seller_id
            )
            fake.product_category(
                product_id=sku.product_id,
                category_id=category.id,
                created_by='longt'
            )
            for barcode in barcodes:
                fake.sellable_product_barcode(sku_id=sku.id, barcode=barcode)
            fake.sellable_product_shipping_type(sellable_product_id=sku.id)
            fake.product_variant_images(variant_id=sku.variant_id)
            self.skus.append(sku)

    def __update_barcode(self, sku, barcode):
        suffix = fake.text(5)
        sellable_product_barcode = models.SellableProductBarcode.query.filter(
            models.SellableProductBarcode.sellable_product_id == sku.id,
            models.SellableProductBarcode.barcode == sku.barcode).first()
        sku.barcode = f'{barcode}{suffix}'
        sellable_product_barcode.barcode = f'{barcode}{suffix}'
        models.db.session.commit()
        return barcode

    def test_list_sku_by_keyword_return200_no_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=fake.text(30),
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_list_sku_by_keyword_return200_only_one_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=self.skus[0].barcode,
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1

    def test_list_sku_by_keyword_return200_multiple_skus(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        barcode = fake.text(25)
        self.__update_barcode(self.skus[0], barcode)
        self.__update_barcode(self.skus[1], barcode)
        url = self.generate_url(
            keyword=barcode,
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2

    def test_list_sku_by_barcodes_return200_no_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            barcodes=fake.text(30),
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_list_sku_by_barcodes_return200_only_one_sku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            barcodes=f'{self.skus[0].barcode},{self.skus[0].barcode}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1

    def test_list_sku_by_barcodes_return200_multiple_skus(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            barcodes=f'{self.skus[random.randint(0, 2)].barcode},{self.skus[random.randint(3, 5)].barcode},{self.skus[random.randint(6, 9)].barcode}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
