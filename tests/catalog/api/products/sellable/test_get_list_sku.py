# coding=utf-8
import random

from flask import current_app
from mock import patch

from catalog import models
from catalog.models import EditingStatus
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetSellableProductTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-874'
    FOLDER = '/Skus/getList'

    def url(self):
        return '/skus'

    def method(self):
        return 'GET'

    def setUp(self):
        fake.init_editing_status()
        self.skus = []
        for i in range(10):
            barcodes = [fake.text() for _ in range(2)]
            category = fake.category(seller_id=2)
            sku = fake.sellable_product(
                barcode=barcodes[1],
                category_id=category.id
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

            assert response_data[i]['category']['id'] == expectation_data[i].category.id
            assert response_data[i]['category']['code'] == expectation_data[i].category.code
            assert response_data[i]['category']['name'] == expectation_data[i].category.name
            assert response_data[i]['category']['path'] == expectation_data[i].category.path
            assert response_data[i]['category']['fullPath'] == expectation_data[i].category.full_path

            assert response_data[i]['masterCategory']['id'] == expectation_data[i].master_category.id
            assert response_data[i]['masterCategory']['code'] == expectation_data[i].master_category.code
            assert response_data[i]['masterCategory']['name'] == expectation_data[i].master_category.name
            assert response_data[i]['masterCategory']['path'] == expectation_data[i].master_category.path
            assert response_data[i]['masterCategory' \
                                    '']['fullPath'] == expectation_data[i].master_category.full_path

    def generate_url(self, **kwargs):
        url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}'
        if not kwargs.get('platformIds'):
            url += '&platformId=1'
        if not kwargs.get('sellerIds'):
            seller_ids = ','.join([str(sku.seller_id) for sku in self.skus])
            url += f'&sellerIds={seller_ids}'
        for key, value in kwargs.items():
            if key not in ("page", "pageSize"):
                url += f'&{key}={value}'
        return url

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_getListSkus_withoutFilter(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url()
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 10
        self.assert_body(body['result']['products'], self.skus)

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_getListSkus_withAllFilter(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
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
            sellerIds=f'{self.skus[0].seller_id}',
            page=1,
            pageSize=11
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 11
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProductIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            productIds=f'{self.skus[0].product_id},{self.skus[1].product_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProductIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            productIds=f'{self.skus[0].product_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProductIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            productIds=f'{self.skus[0].product_id},{self.skus[1].product_id},{self.skus[2].product_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProductIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            productIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByVariantIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            variantIds=f'{self.skus[0].variant_id},{self.skus[1].variant_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByVariantIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            variantIds=f'{self.skus[0].variant_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByVariantIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            variantIds=f'{self.skus[0].variant_id},{self.skus[1].variant_id},{self.skus[2].variant_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByVariantIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            variantIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySkus_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            skus=f'{self.skus[0].sku},{self.skus[1].sku},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySkus_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            skus=f'{self.skus[0].sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySkus_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            skus=f'{self.skus[0].sku},{self.skus[1].sku},{self.skus[2].sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySkus_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            skus='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    def test_200_filterByKeyword_specialCharacter(self):
        # sellable = fake.sellable_product('tiền')
        # url = self.generate_url(
        #     keyword=f'tien',
        # )
        # code, body = self.call_api(url=url)
        # assert code == 200
        # assert body['result']['page'] == 1
        # assert body['result']['pageSize'] == 10
        # assert body['result']['totalRecords'] == 1
        # self.assert_body(body['result']['products'], [sellable])
        pass

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_normalCharacter(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=f'{self.skus[0].name}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    def test_200_filterByKeyword_sensitiveAndInsensitive(self):
        # sellable = fake.sellable_product('tiền')
        # url = self.generate_url(
        #     keyword=f'TIền',
        # )
        # code, body = self.call_api(url=url)
        # assert code == 200
        # assert body['result']['page'] == 1
        # assert body['result']['pageSize'] == 10
        # assert body['result']['totalRecords'] == 1
        # self.assert_body(body['result']['products'], [sellable])
        pass

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_inputCorrectSku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=f'{self.skus[0].sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_inputCorrectSellerSku(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=f'{self.skus[0].seller_sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_inputSkuSplitbyComma(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=f'{self.skus[0].sku},{self.skus[1].sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_aHalfSku_returnEmpty(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        category = fake.category()
        fake.sellable_product(sku='123456789', seller_id=category.seller_id)
        url = self.generate_url(
            keyword='12345',
            sellerIds=f'{category.seller_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_wordAndSkuSplitByComma(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword=f'{self.skus[0].name},{self.skus[1].sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[1:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_withNoResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword='100000000000000000000',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByKeyword_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            keyword='12323333333333333',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByCategoryIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            categoryIds=f'{self.skus[0].category_id},{self.skus[1].category_id},100000',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByCategoryIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            categoryIds=f'{self.skus[0].category_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByCategoryIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            categoryIds=f'{self.skus[0].category_id},{self.skus[1].category_id},{self.skus[2].category_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByCategoryIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            categoryIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByMasterCategoryIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            masterCategoryIds=f'{self.skus[0].master_category_id},{self.skus[1].master_category_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByMasterCategoryIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            masterCategoryIds=f'{self.skus[0].master_category_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByMasterCategoryIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            masterCategoryIds=f'{self.skus[0].master_category_id},{self.skus[1].master_category_id},{self.skus[2].master_category_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByMasterCategoryIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            masterCategoryIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProviderIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            providerIds=f'{self.skus[0].provider_id},{self.skus[1].provider_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProviderIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            providerIds=f'{self.skus[0].provider_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProviderIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            providerIds=f'{self.skus[0].provider_id},{self.skus[1].provider_id},{self.skus[2].provider_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByProviderIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            providerIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByBrandIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            brandIds=f'{self.skus[0].brand_id},{self.skus[1].brand_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByBrandIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            brandIds=f'{self.skus[0].brand_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByBrandIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            brandIds=f'{self.skus[0].brand_id},{self.skus[1].brand_id},{self.skus[2].brand_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByBrandIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            brandIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByEditingStatusCode(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        fake.sellable_product(editing_status_code='approved')
        url = self.generate_url(
            editingStatusCodes=f'approved',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] > 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByEditingStatusCode_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        fake.sellable_product(editing_status_code='approved')
        url = self.generate_url(
            editingStatusCodes='approved,draft,string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] > 2

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByEditingStatusCode_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            editingStatusCodes='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerIds=f'{self.skus[0].seller_id},{self.skus[1].seller_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerIds=f'{self.skus[0].seller_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerIds=f'{self.skus[0].seller_id},{self.skus[1].seller_id},{self.skus[2].seller_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerSkus_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerSkus=f'{self.skus[0].seller_sku},{self.skus[1].seller_sku},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerSkus_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerSkus=f'{self.skus[0].seller_sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerSkus_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerSkus=f'{self.skus[0].seller_sku},{self.skus[1].seller_sku},{self.skus[2].seller_sku}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterBySellerSkus_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            sellerSkus='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByAttributeSetIds_1ParamNotExist_return2RemainCorrectParam(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            attributeSetIds=f'{self.skus[0].attribute_set_id},{self.skus[1].attribute_set_id},string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 2
        self.assert_body(body['result']['products'], self.skus[:2])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByAttributeSetIds_with1Param(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            attributeSetIds=f'{self.skus[0].attribute_set_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 1
        self.assert_body(body['result']['products'], self.skus[:1])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByAttributeSetIds_returnCorrectSkuIn3Params(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            attributeSetIds=f'{self.skus[0].attribute_set_id},{self.skus[1].attribute_set_id},{self.skus[2].attribute_set_id}',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 3
        self.assert_body(body['result']['products'], self.skus[:3])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_filterByAttributeSetIds_invalidFormat_emptyResult(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            attributeSetIds='string',
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 0

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_pageAndPageSizeDefault(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url()
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 10
        self.assert_body(body['result']['products'], self.skus)

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_page1Size2(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            page=1,
            pageSize=2
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 1
        assert body['result']['pageSize'] == 2
        assert body['result']['totalRecords'] == 10
        self.assert_body(body['result']['products'], self.skus[8:10])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_page2Size1(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            page=2,
            pageSize=1
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 2
        assert body['result']['pageSize'] == 1
        assert body['result']['totalRecords'] == 10
        self.assert_body(body['result']['products'], self.skus[8:9])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_pageAndSizeLargerThanTotalRecords(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            page=100
        )
        code, body = self.call_api(url=url)
        assert code == 200
        assert body['result']['page'] == 100
        assert body['result']['pageSize'] == 10
        assert body['result']['totalRecords'] == 10
        assert len(body['result']['products']) == 0


class GetSellableProductBarcodesTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-883'
    FOLDER = '/Skus/getList/barcodes'

    def url(self):
        return '/skus'

    def method(self):
        return 'GET'

    def setUp(self):
        self.category = fake.category()
        self.sku = fake.sellable_product(seller_id=self.category.seller_id)
        fake.product_category(
            product_id=self.sku.product_id,
            category_id=self.category.id,
            created_by='longt'
        )
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def _set_barcodes(self, barcodes):
        self.sku.barcode = barcodes[-1]
        self.sku_barcodes = [fake.sellable_product_barcode(sku_id=self.sku.id, barcode=barcode) for barcode in barcodes]
        models.db.session.flush()
        models.db.session.commit()

    def generate_url(self, **kwargs):
        url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}'
        for key, value in kwargs.items():
            url += f'&{key}={value}'
        return url

    def _equal(self, response_data):
        self.assertEqual(self.sku.barcodes, response_data['barcode'])
        self.assertListEqual(
            list(map(lambda x: {'barcode': x['barcode'], 'source': x['source'], 'isDefault': x['is_default']},
                     self.sku.barcodes_with_source)), response_data['barcodes'])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_get_list_skus_without_barcodes(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        url = self.generate_url(
            skus=f'{self.sku.sku}',
            sellerIds=f'{self.sku.seller_id}',
            platformId='1'
        )
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)
        self._equal(body['result']['products'][0])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_get_list_skus_with_only_one_barcode(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        barcodes = [fake.text(30)]
        self._set_barcodes(barcodes)
        url = self.generate_url(
            skus=f'{self.sku.sku}',
            sellerIds=f'{self.sku.seller_id}',
            platformId='1'
        )
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)
        self._equal(body['result']['products'][0])

    @patch('catalog.services.products.sku.get_default_platform_owner_of_seller')
    @patch('catalog.services.products.sku.get_platform_owner')
    def test_200_get_list_skus_with_multiple_barcodes(self, mock_platform_owner, mock_default_platform_owner):
        mock_platform_owner.return_value = 2
        mock_default_platform_owner.return_value = 1
        barcodes = [fake.text(30) for _ in range(random.randint(2, 20))]
        self._set_barcodes(barcodes)
        url = self.generate_url(
            skus=f'{self.sku.sku}',
            sellerIds=f'{self.sku.seller_id}',
            platformId='1'
        )
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)
        self._equal(body['result']['products'][0])
