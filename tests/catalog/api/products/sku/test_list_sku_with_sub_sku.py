# coding=utf-8
import funcy
import logging

from catalog import models
from tests.faker import fake
from tests.catalog.api import APITestCase
from catalog.constants import SUB_SKU_POSTFIX, MAX_SUB_SKU

__author__ = 'Dung.BV'

_logger = logging.getLogger(__name__)


class TestListSkuWithSubSku(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1599'
    FOLDER = '/Sku/ListSkus/SearchSubSKU'

    def url(self):
        return '/skus'

    def method(self):
        return 'GET'

    def generate_url(self, query_string=None):
        url = None
        if query_string:
            url = '{}?skus={}'.format(self.url(), query_string)
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
            fake.sub_sku(sku, '{}_SUB_1'.format(sku.sku))
            self.skus.append(sku)

    def test_one_subSKU_in_query_return200(self):
        sub_sku = models.SellableProductSubSku.query.first()
        url = self.generate_url(sub_sku.sub_sku)
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        assert len(body['result']['products']) == 1
        sku = body['result']['products'].pop()
        assert sku['sku'] == sub_sku.sub_sku
        assert sku['sellerSku'] == sub_sku.sub_sku
        assert sku['id'] == sub_sku.id
        a = models.SellableProduct.query.get(sub_sku.sellable_product_id)
        assert a.seller_sku != sub_sku.sub_sku

    def test_multiple_subSKU_in_query_return200(self):
        total = models.SellableProductSubSku.query.count()
        fake_total = fake.integer(max=total)
        sub_skus = models.SellableProductSubSku.query.limit(fake_total).all()
        url = self.generate_url(','.join(funcy.lpluck_attr('sub_sku', sub_skus)))
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == max(fake_total, 10)
        assert body['result']['totalRecords'] == fake_total
        assert len(body['result']['products']) == fake_total

    def test_not_subSKU_in_query_return200(self):
        url = self.generate_url(fake.text())
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0
        assert len(body['result']['products']) == 0

    def test_multiple_subSub_of_one_sku(self):
        sellable = models.SellableProduct.query.first()
        fake_total = fake.integer(MAX_SUB_SKU - 1)
        for counter in range(fake_total):
            fake.sub_sku(sellable, '{}{}{}'.format(sellable.sku, SUB_SKU_POSTFIX, counter + 2))
        sub_skus = models.SellableProductSubSku.query.filter(
            models.SellableProductSubSku.sellable_product_id == sellable.id
        ).all()
        url = self.generate_url(','.join(funcy.lpluck_attr('sub_sku', sub_skus)))
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == max(10, len(sub_skus))
        assert body['result']['totalRecords'] == len(sub_skus)
        assert len(body['result']['products']) == len(sub_skus)

    def test_subSKU_and_nonSub_in_query_return200(self):
        sellable = models.SellableProduct.query.first()
        fake_total = fake.integer(MAX_SUB_SKU - 1)
        for counter in range(fake_total):
            fake.sub_sku(sellable, '{}{}{}'.format(sellable.sku, SUB_SKU_POSTFIX, counter + 2))
        sub_skus = models.SellableProductSubSku.query.filter(
            models.SellableProductSubSku.sellable_product_id == sellable.id
        ).all()
        all_sku = models.SellableProduct.query.all()
        url = self.generate_url(','.join(funcy.lpluck_attr('sub_sku', sub_skus)))
        url = '{},{}'.format(url, ','.join(funcy.lpluck_attr('sku', all_sku)))
        code, body = self.call_api(url=url)
        total = len(sub_skus) + len(all_sku)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == total
        assert body['result']['totalRecords'] == total
        assert len(body['result']['products']) == total

    def test_result_subSKU(self):
        sellable = models.SellableProduct.query.first()
        fake.sub_sku(sellable, '{}{}{}'.format(sellable.sku, SUB_SKU_POSTFIX, 2))
        sub_skus = models.SellableProductSubSku.query.filter(
            models.SellableProductSubSku.sellable_product_id == sellable.id
        ).all()
        url = self.generate_url(','.join(funcy.lpluck_attr('sub_sku', sub_skus)))
        url = '{},{}'.format(url, sellable.sku)
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        assert len(body['result']['products']) == 3
        assert funcy.lpluck_attr('sub_sku', sub_skus) + [sellable.sku] == funcy.lpluck('sku',
                                                                                       body['result']['products'])
