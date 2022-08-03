# coding=utf-8
from catalog import models
from catalog.models import db
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class SetupUpdateProductCommon(APITestCase):
    def setUp(self):
        self.user = fake.iam_user()
        category = fake.category(is_active=True, seller_id=self.user.seller_id)
        self.product = fake.product(
            created_by=self.user.email,
            editing_status_code='draft',
            category_id=category.id
        )
        self.data = {
            'name': fake.name(),
            'categoryId': category.id,
            'masterCategoryId': fake.master_category(is_active=True).id,
            'brandId': fake.brand(is_active=True).id,
            'warrantyMonths': fake.integer(),
            'warrantyNote': fake.text(),
            'type': fake.misc(data_type='product_type', code=fake.text(5)).code,
            'taxInCode': fake.tax().code,
            'taxOutCode': fake.tax().code,
            'model': fake.text(),
            'detailedDescription': fake.text(),
            'description': fake.text()
        }

    def url(self):
        return '/products/{}'

    def method(self):
        return 'PATCH'

    def assertProductData(self, data, product):
        for key, value in data.items():
            if hasattr(product, key):
                assert getattr(product, key) == value


class UpdateProductCommonAPITestCase(SetupUpdateProductCommon):
    # ISSUE_KEY = 'SC-574'
    ISSUE_KEY = 'SC-651'

    def test_passValidData__returnJSONOfProductCommon(self):
        for i in range(2):
            fake.product_variant(
                product_id=self.product.id,
                name=f'{self.product.name} ({i})'
            )

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(code, 200)
            self.assertEqual(body['code'], 'SUCCESS')
            self.assertIsNotNone(body['result'])

            self.assertProductData(
                self.data,
                models.Product.query.get(body['result']['id'])
            )

            variants = models.ProductVariant.query.filter_by(
                product_id=self.product.id
            ).all()

            for i in range(len(variants)):
                self.assertEqual(variants[i].name, f'{self.data["name"]} ({i})')

    def test_passInvalidProductDraftUser__returnBadRequest(self):
        product = fake.product(created_by=fake.iam_user().email, editing_status_code='draft')
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product.id), data=self.data)
        self.assertEqual(code, 400)
        self.assertEqual(body['message'], f'Không tồn tại sản phẩm có id là {product.id}')

    def test_passNotDraftProduct__returnBadRequest(self):
        self.product.editing_status_code = 'active'
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body['message'],
                             "Sản phẩm không có trạng thái biên tập là đang nháp. Bạn không thể sửa thông tin")

    def test_passNullInRequiredField__returnBadRequest(self):
        self.data['name'] = None
        self.data['categoryId'] = None
        self.data['brandId'] = None
        self.data['warrantyMonths'] = None
        self.data['type'] = None
        self.data['taxInCode'] = None
        self.data['taxOutCode'] = None

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(len(body['result']), 6)

    def test_passTooShortOrTooSmallFieldValue__returnBadRequest(self):
        self.data['name'] = ''
        self.data['warrantyMonths'] = -1
        self.data['type'] = ''

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(len(body['result']), 3)

    def test_passFieldTooLongOrTooLarge__returnBadRequest(self):
        self.data['name'] = 'a' * 266
        self.data['detailedDescription'] = 'a' * 70002
        self.data['description'] = 'a' * 502
        self.data['warrantyNote'] = 'a' * 266
        self.data['model'] = 'a' * 266
        self.data['warrantyMonths'] = 10000
        self.data['taxInCode'] = 'a' * 11
        self.data['taxOutCode'] = 'a' * 11
        self.data['type'] = 'a' * 31

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['code'], 'INVALID')
            self.assertEqual(len(body['result']), 9)

    def test_passNotUniqueName__returnBadRequest(self):
        """
        Update the requirement
        Allow the same name in the system
        Jira Ticket CATALOGUE-302

        """
        fake.product(name=self.data['name'])

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 200)

        data = self.data.copy()
        data['name'] = '  Áo Quần   '
        fake.product(name='áo quần')
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=data)
            self.assertEqual(code, 200)

    def test_passNotLeafNodeCategoryId__returnBadRequest(self):
        category = fake.category(is_active=True, seller_id=self.user.seller_id)
        self.data['categoryId'] = category.id
        fake.category(is_active=True, parent_id=category.id, path=f'{category.id}')

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400, body)
            self.assertEqual(body['message'], 'Vui lòng chọn danh mục ngành hàng là nút lá')

    def test_passInactiveField__returnBadRequest(self):
        category = fake.category(is_active=False, seller_id=self.user.seller_id)
        brand = fake.brand(is_active=False)
        db.session.commit()

        list_fields = [
            ['categoryId', category.id],
            ['brandId', brand.id]
        ]

        error_message_lists = [
            "Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại",
            "Thương hiệu đang bị vô hiệu, vui lòng chọn lại"
        ]
        for index in range(len(list_fields)):
            field, value = list_fields[index]
            error_message = error_message_lists[index]

            data = self.data.copy()
            data[field] = value

            with logged_in_user(self.user):
                code, body = self.call_api(url=self.url().format(self.product.id), data=data)

                self.assertEqual(code, 400, body)
                self.assertEqual(body['message'], error_message)

    def test_passNotExistField__returnBadRequest(self):
        list_fields = ['categoryId', 'brandId', 'taxInCode', 'taxOutCode', 'type']
        values = [100, 100, '-1', '-1', '-1']
        error_message_lists = [
            "Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại",
            "Thương hiệu không tồn tại, vui lòng chọn lại",
            "Mã thuế vào không tồn tại",
            "Mã thuế ra không tồn tại",
            "Không tồn tại mã loại hình sản phẩm"
        ]

        for index in range(len(list_fields)):
            field = list_fields[index]
            error_message = error_message_lists[index]

            data = self.data.copy()
            data[field] = values[index]

            with logged_in_user(self.user):
                code, body = self.call_api(url=self.url().format(self.product.id), data=data)

                self.assertEqual(code, 400)
                self.assertEqual(body['message'], error_message)

    def test_passNonIntegerWarrantyMonths__returnBadRequest(self):
        self.data['warrantyMonths'] = 'abc'
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body['result'][0]['field'], 'warrantyMonths')

    def test_passEmptyInRequiredField__returnBadRequest(self):
        self.data['type'] = ""

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(len(body['result']), 1)

    def test_passNullInNotRequiredField__returnUpdatedSuccessfully(self):
        self.data['model'] = None
        self.data['warrantyNote'] = None
        self.data['description'] = None
        self.data['detailedDescription'] = None

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 200)
            self.assertProductData(
                self.data,
                models.Product.query.get(body['result']['id'])
            )

    def test_passEmptyInNotRequiredField__returnUpdatedSuccessfully(self):
        self.data['model'] = ""
        self.data['warrantyNote'] = ""
        self.data['description'] = ""
        self.data['detailedDescription'] = ""

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 200, body)
            self.assertProductData(
                self.data,
                models.Product.query.get(body['result']['id'])
            )

    def test_passTaxInIsBundleProduct__returnBadRequest(self):
        product = fake.product(is_bundle=True, created_by=self.user.email, editing_status_code='draft')
        self.data = {
            'taxOutCode': fake.tax().code
        }

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Không nhập mã thuế ra đối với sản phẩm bundle')

        self.data = {
            'taxInCode': fake.tax().code
        }

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Không nhập mã thuế vào đối với sản phẩm bundle')

        self.data = {
            'taxInCode': ''
        }
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Vui lòng bổ sung Thuế mua vào')

    def test_passEmptyPayload__returnBadRequest(self):
        self.data = {}

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Empty payload is not permitted')


class TestAllowMasterCategoryNone(SetupUpdateProductCommon):
    ISSUE_KEY = 'CATALOGUE-251'
    FOLDER = '/Product/Update'

    def test_updateProduct_passExistMasterCategoryId_200_updateSuccessfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(200, code)

    def test_updateProduct_passNoneMasterCategoryId_200_updateSuccessfully(self):
        self.data['masterCategoryId'] = None
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(200, code)

        product = models.Product.query.get(self.product.id)
        self.assertIsNone(product.master_category_id)

    def test_updateProduct_notPassMasterCategoryId_200_updateSuccessfully(self):
        del self.data['masterCategoryId']

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(200, code)

    def test_updateProduct_400_masterCategoryNotExist(self):
        self.data['masterCategoryId'] = 123
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.product.id), data=self.data)
            self.assertEqual(400, code)
