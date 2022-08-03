# coding=utf-8

import random

from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestListSKU(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1471'
    FOLDER = '/Sku/ListSkus/SearchByModels'

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
            model = fake.text(10)
            product = fake.product(model=model)
            category = fake.category()
            variant = fake.product_variant(product_id=product.id)
            sku = fake.sellable_product(
                seller_id=category.seller_id,
                model=model,
                variant_id=variant.id
            )
            fake.product_category(
                product_id=sku.product_id,
                category_id=category.id,
                created_by='thuctm'
            )
            fake.sellable_product_shipping_type(sellable_product_id=sku.id)
            fake.product_variant_images(variant_id=sku.variant_id)
            self.skus.append(sku)

    def __update_model(self, sku, model):
        sellable_product_model = models.SellableProduct.query.filter().first()
        sku.model = model
        sellable_product_model.model = model
        models.db.session.commit()
        return model

    def test_list_sku_by_model_return200_no_sku(self):
        url = self.generate_url(
            models=fake.text(10),
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_list_sku_by_2_model_return200_no_sku(self):
        url = self.generate_url(
            models='1,2'
        )
        code, body = self.call_api(url=url)
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_list_sku_by_2_model_return200_only_one_sku(self):
        model_query = self.skus[0].model
        url = self.generate_url(
            models=f'{model_query}, 1',
        )

        code, body = self.call_api(url=url)
        firstProduct = body['result']['products'][0]
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        assert firstProduct['model'] == model_query

    def test_list_sku_by_model_return200_multiple_skus(self):

        model = fake.text(25)
        self.__update_model(self.skus[0], model)
        self.__update_model(self.skus[1], model)
        url = self.generate_url(
            models=model,
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2

    def test_list_sku_by_multi_model_return200_multiple_skus(self):

        model = fake.text(25)
        model2 = fake.text(25)
        self.__update_model(self.skus[0], model)
        self.__update_model(self.skus[1], model2)
        url = self.generate_url(
            models=f'{model2},{model}',
        )
        code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2

    def test_list_sku_by_multi_atleast_an_empty_model_return400(self):

        model = fake.text(25)
        model2 = fake.text(25)
        url = self.generate_url(
            models=f'{model2},{model},,',
        )
        code, body = self.call_api(url=url)
        assert code == 400
