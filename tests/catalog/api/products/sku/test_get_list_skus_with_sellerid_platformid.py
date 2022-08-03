import logging
import random

from flask import current_app

from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'long.t'
_logger_ = logging.getLogger(__name__)

class TestGetListSkus(APITestCase):
    # ISSUE_KEY = 'CATALOGUE-1141'
    ISSUE_KEY = 'CATALOGUE-1347'
    FOLDER = '/Sku/ListSkus/SearchBySellerAndPlatform'

    def url(self):
        return 'skus'

    def method(self):
        return 'GET'

    def setUp(self):
        fake.init_editing_status()
        self.skus = []
        self.sellers = [fake.seller() for _ in range(0,10)]
        self.seller = self.sellers[1]
        self.platform_ids = [fake.integer() for _ in range(0,10)]
        self.categories = []
        self.skus = []
        fake.platform_sellers(self.sellers[0].id, self.platform_ids[0], is_default=True, is_owner=True)
        self.categories.append(fake.category(seller_id=self.sellers[0].id))
        for seller in self.sellers[1:]:
            fake.platform_sellers(seller.id, platform_id=self.platform_ids[1], is_default=True)
            self.categories.append(fake.category(seller_id=self.seller.id))
        for platform_id in self.platform_ids:
            fake.platform_sellers(self.seller.id, platform_id, is_owner=True)
        for i in range(0,10):
            cat_id = random.choice(self.categories[1:]).id
            sku = fake.sellable_product(seller_id=random.choice(self.sellers[1:]).id, category_id=cat_id)
            fake.product_category(product_id=sku.product_id, category_id=cat_id)
            fake.product_category(product_id=sku.product_id, category_id=self.categories[0].id)
            fake.sellable_product_barcode(sku_id=sku.id)
            fake.sellable_product_shipping_type(sellable_product_id=sku.id)
            fake.product_variant_images(variant_id=sku.variant_id)
            self.skus.append(sku)

        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def assert_body(self, response_data, expectation):
        expectation_data = expectation[::-1]

        for i in range(len(response_data)):
            assert response_data[i]['id'] == expectation_data[i].id
            assert response_data[i]['sku'] == expectation_data[i].sku
            assert response_data[i]['sellerSku'] == expectation_data[i].seller_sku
            assert response_data[i]['name'] == expectation_data[i].name
            assert response_data[i]['model'] == expectation_data[i].model
            assert ','.join(response_data[i]['barcode']) == ','.join(expectation_data[i].barcodes)
            assert response_data[i]['warrantyMonths'] == expectation_data[i].warranty_months
            assert response_data[i]['trackingType'] == expectation_data[i].tracking_type
            assert response_data[i]['expiryTracking'] == expectation_data[i].expiry_tracking
            assert response_data[i]['expirationType'] == expectation_data[i].expiration_type
            assert response_data[i]['daysBeforeExpLock'] == expectation_data[i].days_before_exp_lock
            assert response_data[i]['partNumber'] == expectation_data[i].part_number
            assert response_data[i]['productType'] == expectation_data[i].product_type
            assert response_data[i]['uomName'] == expectation_data[i].uom_name
            assert response_data[i]['uomCode'] == expectation_data[i].uom_code
            assert response_data[i]['uomRatio'] == expectation_data[i].uom_ratio
            assert response_data[i]['taxInCode'] == expectation_data[i].tax_in_code
            assert response_data[i]['variantId'] == expectation_data[i].variant_id
            assert response_data[i]['providerId'] == expectation_data[i].provider_id
            assert response_data[i]['productId'] == expectation_data[i].product_id
            assert response_data[i]['sellerId'] == expectation_data[i].seller_id
            assert response_data[i]['shippingTypeId'] == expectation_data[i].shipping_types[0].id

            assert response_data[i]['productName'] == expectation_data[i].product.name
            assert response_data[i]['urlKey'] == expectation_data[i].product_variant.url_key

            assert response_data[i]['images'][0]['url'] == expectation_data[i].product_variant.images[0].url
            assert response_data[i]['images'][0]['altText'] == expectation_data[i].product_variant.images[0].label
            assert response_data[i]['images'][0]['allowDisplay'] == expectation_data[i].product_variant.images[
                0].is_displayed

            assert response_data[i]['brand']['id'] == expectation_data[i].brand.id
            assert response_data[i]['brand']['name'] == expectation_data[i].brand.name
            assert response_data[i]['brand']['code'] == expectation_data[i].brand.code
            assert response_data[i]['brand']['logo'] == expectation_data[i].brand.path

            assert response_data[i]['editingStatus']['name'] == expectation_data[i].editing_status.name
            assert response_data[i]['editingStatus']['code'] == expectation_data[i].editing_status.code
            assert response_data[i]['editingStatus']['config'] == expectation_data[i].editing_status.config

            assert response_data[i]['attributeSet']['id'] == expectation_data[i].attribute_set.id
            assert response_data[i]['attributeSet']['name'] == expectation_data[i].attribute_set.name
            assert response_data[i]['attributeSet']['code'] == expectation_data[i].attribute_set.code

            assert response_data[i]['masterCategory']['id'] == expectation_data[i].master_category.id
            assert response_data[i]['masterCategory']['code'] == expectation_data[i].master_category.code
            assert response_data[i]['masterCategory']['name'] == expectation_data[i].master_category.name
            assert response_data[i]['masterCategory']['path'] == expectation_data[i].master_category.path

            assert response_data[i]['defaultCategory']['id'] == expectation_data[i].default_category.id
            assert response_data[i]['defaultCategory']['code'] == expectation_data[i].default_category.code
            assert response_data[i]['defaultCategory']['name'] == expectation_data[i].default_category.name
            assert response_data[i]['defaultCategory']['path'] == expectation_data[i].default_category.path

            assert response_data[i]['category']['id'] == expectation_data[i].platform_category.id
            assert response_data[i]['category']['code'] == expectation_data[i].platform_category.code
            assert response_data[i]['category']['name'] == expectation_data[i].platform_category.name
            assert response_data[i]['category']['path'] == expectation_data[i].platform_category.path

    def assert_category_equal_default_category(self, expectation_datas):
        for exp in expectation_datas:
            assert exp.category == exp.default_category

    def assert_category_is_from_item_seller(self, expectation_datas):
        for exp in expectation_datas:
            assert exp.category == exp.default_category
            assert exp.category.seller_id == self.seller.id

    def generate_url(self, **kwargs):
        url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}'
        for key, value in kwargs.items():
            if key not in ("page", "pageSize"):
                url += f'&{key}={value}'
        return url

    def test_GetListSkus__return_200_seller_category__with_SellerId_PlatformId(self):
        url = self.generate_url(
            platformId=str(self.platform_ids[0]),
            sellerIds=','.join([str(seller.id) for seller in self.sellers])
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 10
        self.assert_body(body['result']['products'], self.skus[:10:1])

    def test_GetListSkus__return_200_seller_platform_category__with_SellerId_but_no_PlatformId(self):
        seller_ids = ','.join([str(seller.id) for seller in self.sellers])
        url = self.generate_url(
            sellerIds=f'{seller_ids}',
            page=1,
            pageSize=11
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 11
        assert body['result']['totalRecords'] == 10
        expectation_datas = self.skus[:10:1]
        self.assert_body(body['result']['products'], expectation_datas)
        self.assert_category_equal_default_category(expectation_datas)


    def test_GetListSkus__return_200_with_PlatformId_but_no_SellerId(self):
        url = self.generate_url(
            productIds=f'{self.skus[0].product_id}',
            variantIds=f'{self.skus[0].variant_id}',
            attributeSetIds=f'{self.skus[0].attribute_set_id}',
            skus=f'{self.skus[0].sku}',
            sellerSkus=f'{self.skus[0].seller_sku}',
            keyword=f'{self.skus[0].name}',
            categoryIds=f'{self.skus[0].category_id}',
            masterCategoryIds=f'{self.skus[0].master_category_id}',
            providerIds=f'{self.skus[0].provider_id}',
            brandIds=f'{self.skus[0].brand_id}',
            editingStatusCodes=f'{self.skus[0].editing_status_code}',
            platformId=self.platform_ids[0],
            page=1,
            pageSize=11
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 11
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[0:1])

    def test_GetListSkus__return_200__without_SellerId_PlatformId(self):
        url = self.generate_url(
            page=1,
            pageSize=11
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 11
        assert body['result']['totalRecords'] == 10
        expectation_datas = self.skus[:10:1]
        self.assert_body(body['result']['products'], expectation_datas)
        self.assert_category_equal_default_category(expectation_datas)
        self.assert_category_is_from_item_seller(expectation_datas)
