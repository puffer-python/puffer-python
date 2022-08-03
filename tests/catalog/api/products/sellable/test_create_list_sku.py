# coding=utf-8
from unittest.mock import patch

from flask import current_app

from catalog import models
from catalog.api.product.sku.create_list_sku_schema import CreateListSkuRequest
from tests.catalog.api import APITestCase
from tests.faker import fake


class CreateListSku(APITestCase):
    ISSUE_KEY = 'CATALOGUE-631'
    FOLDER = '/Skus/createList'

    def setUp(self):
        self.seller = fake.seller()
        self.data = self.fake_data()
        self.product = fake.product()
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def fake_data(self):
        attribute_set = fake.attribute_set()
        return {
            'sellerId': self.seller.id,
            'productName': fake.name(),
            'masterCategoryId': fake.master_category(is_active=True).id,
            'categoryId': fake.category(is_active=True, seller_id=self.seller.id, attribute_set_id=attribute_set.id).id,
            'attributeSetId': attribute_set.id,
            'brandId': fake.brand(is_active=True).id,
            'providerId': 1,
            'model': fake.text(),
            'taxInCode': fake.tax().code,
            'detailedDescription': fake.text(),
            'description': fake.text(),
            'warrantyMonths': fake.integer(),
            "createdBy": fake.email()
        }

    def assert_product_data(self, data, product):
        data = CreateListSkuRequest().load(data)
        for key, value in data.items():
            if hasattr(product, key):
                assert getattr(product, key) == value

    def test_200_createSuccessfully(self):
        code, body = self.call_api(data=self.data)
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assert_product_data(
            self.data,
            models.Product.query.get(body['result']['productId'])
        )

    @patch('catalog.services.seller.get_seller_by_id')
    def test_400_sellerId_notExist(self, mock_seller):
        mock_seller.return_value = {}
        self.data['sellerId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Seller không tồn tại'

    def test_400_masterCategoryId_notExist(self):
        self.data['masterCategoryId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Danh mục sản phẩm không tồn tại trên hệ thống, vui lòng chọn lại'

    def test_400_masterCategoryId_inactive(self):
        self.data['masterCategoryId'] = fake.master_category(is_active=False).id
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Danh mục sản phẩm đang bị vô hiệu, vui lòng chọn lại'

    def test_400_masterCategoryId_notTheLeafNode(self):
        parent_master_category = fake.master_category(is_active=True)
        fake.master_category(parent_id=parent_master_category.id, is_active=True).id
        self.data['masterCategoryId'] = parent_master_category.id
        code, body = self.call_api(data=self.data)

        assert 400 == code
        assert body['message'] == 'Vui lòng chọn danh mục sản phẩm là nút lá'

    def test_400_categoryId_notExist(self):
        self.data['categoryId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại'

    def test_400_categoryId_inactive(self):
        self.data['categoryId'] = fake.category(seller_id=self.seller.id, is_active=False).id
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại'

    def test_400_categoryId_notTheLeafNode(self):
        parent_category = fake.category(seller_id=self.seller.id, is_active=True)
        fake.category(seller_id=self.seller.id, parent_id=parent_category.id, is_active=True).id
        self.data['categoryId'] = parent_category.id
        code, body = self.call_api(data=self.data)

        assert 400 == code
        assert body['message'] == 'Vui lòng chọn danh mục ngành hàng là nút lá'

    def test_400_attributeSetId_notExist(self):
        self.data['attributeSetId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Bộ thuộc tính không tồn tại'

    def test_400_brandId_notExist(self):
        self.data['brandId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Thương hiệu không tồn tại, vui lòng chọn lại'

    def test_400_brandId_inactive(self):
        self.data['brandId'] = fake.brand(is_active=False).id
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Thương hiệu đang bị vô hiệu, vui lòng chọn lại'

    def test_400_providerId_notExist(self):
        self.data['sellerId'] = 15
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Nhà cung cấp không hợp lệ'

    def test_400_taxInCode_notExist(self):
        self.data['taxInCode'] = self.data['taxInCode'] + fake.text()
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == 'Mã thuế vào không tồn tại'

    def test_400_detailedDescription_largerThan70000(self):
        self.data['detailedDescription'] = ''.join(['a' for _ in range(70001)])
        code, body = self.call_api(data=self.data)
        assert 400 == code

    def test_400_description_largerThan500(self):
        self.data['description'] = ''.join(['a' for _ in range(501)])
        code, body = self.call_api(data=self.data)
        assert 400 == code

    def test_200_updateSuccessfully(self):
        code, body = self.call_api(data=self.data)
        assert 200 == code

        data = self.fake_data()
        data['productId'] = body['result']['productId']
        code, body = self.call_api(data=data)
        assert 200 == code
        assert 'SUCCESS' == body['code']
        self.assert_product_data(
            data,
            models.Product.query.get(body['result']['productId'])
        )

    def test_400_productId_notExist(self):
        self.data['productId'] = 10
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert body['message'] == f'Không tồn tại sản phẩm có id là {10}'

    def test_200_updateWithoutSellerId(self):
        pass

    def test_200_updateWithoutProductName(self):
        self.data['productId'] = self.product.id
        self.data.pop('productName')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutCategoryId(self):
        self.data['productId'] = self.product.id
        self.data.pop('categoryId')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutMasterCategoryId(self):
        self.data['productId'] = self.product.id
        self.data.pop('masterCategoryId')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutBrandId(self):
        self.data['productId'] = self.product.id
        self.data.pop('brandId')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutAttributeSetId(self):
        self.data['productId'] = self.product.id
        self.data.pop('attributeSetId')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutTaxInCode(self):
        self.data['productId'] = self.product.id
        self.data.pop('taxInCode')
        code, body = self.call_api(data=self.data)
        assert 200 == code

    def test_200_updateWithoutProviderId(self):
        self.data['productId'] = self.product.id
        self.data.pop('providerId')
        code, body = self.call_api(data=self.data)
        assert 200 == code
