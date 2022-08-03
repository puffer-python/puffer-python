# coding=utf-8

from mock import patch
from flask import current_app

from catalog.extensions import exceptions as exc
from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user


class CreateProductCommonAPITestCase(APITestCase):
    # ISSUE_KEY = 'SC-340'
    ISSUE_KEY = 'SC-550'

    def headers(self):
        return self._headers

    def setUp(self):
        self._headers = None
        self.user = fake.iam_user()
        self.data = {
            'name': fake.name(),
            'isBundle': False,
            'masterCategoryId': fake.master_category(is_active=True).id,
            'categoryId': fake.category(is_active=True, seller_id=self.user.seller_id).id,
            'attributeSetId': fake.attribute_set().id,
            'brandId': fake.brand(is_active=True).id,
            'warrantyMonths': fake.integer(),
            'warrantyNote': fake.text(),
            'type': fake.misc(data_type='product_type', code=fake.text(5)).code,
            'taxInCode': fake.tax().code,
            'taxOutCode': fake.tax().code,
            'model': fake.text(),
            'detailedDescription': fake.text(),
            'description': fake.text(),
            'unitId': fake.unit().id
        }

    def url(self):
        return '/products'

    def method(self):
        return 'POST'

    def assertProductData(self, data, product):
        for key, value in data.items():
            if hasattr(product, key):
                assert getattr(product, key) == value

    def test_passValidData__returnJSONOfProductCommon(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            assert 200 == code, self.data['type']
            assert 'SUCCESS' == body['code']
            self.assertProductData(
                self.data,
                models.Product.query.get(body['result']['id'])
            )

    def test_urlKeyNotIncludeSpecialCharacter__returnJSONOfProductCommon(self):
        with logged_in_user(self.user):
            self.data['name'] = 'á ba_,12.c'
            code, body = self.call_api(data=self.data)
            assert 200 == code, self.data['type']
            assert 'SUCCESS' == body['code']

            product = models.Product.query.get(body['result']['id'])
            self.assertEqual(product.url_key, 'a-ba-12-c')

    def test_passNameTooLong__returnErrorResponse(self):
        self.data['name'] = 'a' * 266
        code, body = self.call_api(data=self.data)
        assert 400 == code
        assert 'INVALID' == body['code']
        assert 'name' == body['result'][0]['field']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passNameExisted__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            self.data['name'] = fake.product().name
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    def test_passNameContainSpecialChar__returnJSONOfProductCommon(self):
        with logged_in_user(self.user):
            self.data['name'] = fake.name() + '@#$%'
            code, body = self.call_api(data=self.data)
            assert 200 == code
            assert 'SUCCESS' == body['code']
            self.assertProductData(
                self.data,
                models.Product.query.get(body['result']['id'])
            )

    def test_missingRequireField__returnErrorResponse(self):
        with logged_in_user(self.user):
            self.data.pop('name')
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']
            assert 'name' == body['result'][0]['field']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passBrandInactive__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            mock.side_effect = exc.BadRequestException()
            self.data['brandId'] = fake.brand(is_active=False).id
            code, body = self.call_api(data=self.data)
            assert 400 == code, body
            assert 'INVALID' == body['code']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passBrandNotExist__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            self.data['brandId'] = fake.integer()
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passMasterCategoryInactive__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            self.data['masterCategoryId'] = fake.master_category(is_active=False).id
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passMasterCategoryHasActiveChildren__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            parent_master_category = fake.master_category(is_active=True)
            fake.master_category(parent_id=parent_master_category.id, is_active=True)
            self.data['masterCategoryId'] = parent_master_category.id
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passMasterCategoryHasAllInactiveChildren__raiseBadRequestException(self, mock):
        with logged_in_user(self.user):
            parent_master_category = fake.master_category(is_active=True)
            fake.master_category(parent_id=parent_master_category.id, is_active=False)
            self.data['masterCategoryId'] = parent_master_category.id
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    @patch('catalog.validators.products.ProductCommonValidator.validate')
    def test_passMasterCategoryNotExist__returnErrorResponse(self, mock):
        with logged_in_user(self.user):
            self.data['masterCategoryId'] = fake.integer()
            mock.side_effect = exc.BadRequestException()
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    def test_passModelTooLong__returnErrorResponse(self):
        with logged_in_user(self.user):
            self.data['model'] = 'a' * 256
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']
            assert 'model' == body['result'][0]['field']

    def test_passDescriptionTooLong__returnErrorResponse(self):
        with logged_in_user(self.user):
            self.data['description'] = 'a' * 501
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']
            assert 'description' == body['result'][0]['field']

    def test_passHighLightTooLong__returnErrorResponse(self):
        with logged_in_user(self.user):
            self.data['highlight'] = 'a' * 10001
            code, body = self.call_api(data=self.data)
            assert 400 == code
            assert 'INVALID' == body['code']
            assert 'highlight' == body['result'][0]['field']

    def test_makeInternalAPICallWhileHavingDraftProduct__returnCreateSuccess(self):

        current_app.config.update(INTERNAL_HOST_URLS=['url-stuff.info'])
        # create draft product
        fake.product(editing_status_code='draft')
        self._headers = {
            'X-SELLER-ID': self.user.seller_id
        }
        code, body = self.call_api(data=self.data, url='http://url-stuff.info/products')
        self.assertEqual(200, code, body)
        self.assertProductData(
            self.data,
            models.Product.query.get(body['result']['id'])
        )

    def test_makeInternalAPICallFromOtherService__returnUnauthorizedResponse(self):
        current_app.config.update(INTERNAL_HOST_URLS=['url-stuff.info'])
        code, body = self.call_api(data=self.data, url='http://other-url-stuff.info/products')
        self.assertEqual(401, code)

    def test_makeInternalAPICallWithDraftProductWithoutSettingEnv__returnUnauthorizedResponse(self):
        # create draft product
        current_app.config.update(INTERNAL_HOST_URLS=[])
        product = fake.product(editing_status_code='draft')
        code, body = self.call_api(data=self.data, url='http://url-stuff.info/products')
        self.assertEqual(401, code)
