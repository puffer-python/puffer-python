# coding=utf-8

import logging
import random

import config
import json
from mock import patch
from catalog import models as m, models
from catalog.services.categories import CategoryService
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user

__author__ = 'quang.da'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class CreateCategoryTreeSetup(APITestCase):
    FOLDER = '/Category/Create'

    def url(self):
        return '/categories'

    def method(self):
        return 'POST'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.unit = fake.unit()
        self.tax_in_code = fake.tax(code="10")
        self.tax_out_code = fake.tax(code="5")
        with open(
                '{}/tests/datafiles/category.json'.format(config.ROOT_DIR),
                'r'
        ) as datafile:
            categories = json.load(datafile)
            self.categories = [fake.category_json(**data) for data in categories]

        self.shipping_types = [fake.shipping_type() for _ in range(2)]
        self.master_categories_level_0 = fake.master_category(
            name='Mỹ phẩm - Làm đẹp', is_active=True,
            parent_id=0, seller_id=self.seller.id, attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_1 = fake.master_category(
            name='Chăm sóc tóc', is_active=True,
            parent_id=self.master_categories_level_0.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_2 = fake.master_category(
            name='Dầu gội, dầu xả', is_active=True,
            parent_id=self.master_categories_level_1.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_3 = fake.master_category(
            name='Dầu Gội', is_active=True,
            parent_id=self.master_categories_level_2.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )

        self.payload_body = {
            "code": "DAQ",
            "name": "Dầu",
            "parentId": self.categories[0].id,
            "manageSerial": True,
            "autoGenerateSerial": True,
            "unitId": self.unit.id,
            "taxInCode": self.tax_in_code.code,
            "taxOutCode": self.tax_out_code.code,
            "shippingTypes": [self.shipping_types[0].id, self.shipping_types[1].id],
            "attributeSetId": self.attribute_set.id,
            "masterCategoryId": self.master_categories_level_3.id
        }

        self.patcher_signal = patch('catalog.extensions.signals.ram_category_created_signal.send')
        self.mock_signal = self.patcher_signal.start()

    def tearDown(self):
        self.patcher_signal.stop()


class CreateCategoryTreeTestCase(CreateCategoryTreeSetup):
    ISSUE_KEY = 'CATALOGUE-411'

    def assertBody(self, payload_body, obj_dict):
        for key, value in payload_body.items():
            if key == 'parentId':
                assert obj_dict['parent']['id'] == value
            elif key == 'attributeSetId':
                attribute_set = obj_dict['attributeSet']
                assert attribute_set['id'] == self.attribute_set.id
                assert attribute_set['name'] == self.attribute_set.name
            elif key == 'masterCategory':
                master_category = obj_dict['masterCategory']
                assert master_category['id'] == self.master_categories_level_3.id
                assert master_category['name'] == self.master_categories_level_3.name
                assert master_category['path'] == self.master_categories_level_3.path
                assert master_category['fullPath'] == self.master_categories_level_3.full_path
            elif key == 'shippingTypes':
                obj_shipping_type = obj_dict['shippingTypes']
                self.assertEqual(len(obj_shipping_type), 2)
                self.assertIn(obj_shipping_type[0].get('id'), self.payload_body['shippingTypes'])
                self.assertIn(obj_shipping_type[1].get('id'), self.payload_body['shippingTypes'])
            else:
                assert obj_dict.get(key) == value

    def assertRecommendation(self, body):
        self.assertTrue("attributeSet" in body["result"])
        self.assertTrue("masterCategory" in body["result"])
        self.assertBody(self.payload_body, body["result"])

        category = m.Category.query.filter(
            m.Category.code == self.payload_body.get('code')
        ).first()
        self.assertIsNotNone(category.attribute_set_id)
        self.assertIsNotNone(category.master_category_id)

    def test_passAllParams_200_saveToDBInputtedMasterCategoryAndAttributeSet(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertRecommendation(body)

    def test_inputMasterCategoryIdOnly_200_SaveToDBInputtedMasterCategoryAndAttributeSetWhichMappedWithIt(self):
        del self.payload_body['attributeSetId']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertRecommendation(body)

    def test_inputAttributeSetIdOnly_200_SaveToDBRecommendedMasterCategoryAndInputtedAttributeSet(self):
        del self.payload_body['masterCategoryId']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertRecommendation(body)

    def test_inputNothing_200_masterCategoryAndAttributeSetAreRecommended(self):
        del self.payload_body['masterCategoryId']
        del self.payload_body['attributeSetId']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertRecommendation(body)

    def test_passNullFields_400_fieldsAreNotNull(self):
        payload_body = {
            "code": None,
            "name": None,
            "parentId": self.categories[0].id,
            "manageSerial": True,
            "autoGenerateSerial": fake.boolean(),
            "attributeSetId": self.attribute_set.id,
            "unitId": self.unit.id,
            "taxInCode": None,
            "taxOutCode": None,
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=payload_body)
            self.assertEqual(400, code)

    def test_passManageSerialFalseAndAutoGenerateSerialTrue_400_autoGenerateSerialCanNotBeTrue(self):
        self.payload_body["manageSerial"] = False
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Không set tự động sinh serial nếu quản lí serial là vô hiệu")
            self.assertEqual(400, code)

    def test_passManageSerialTrueAndAutoGenerateSerialNull_400_autoGenerateSerialCanNotBeNull(self):
        self.payload_body["manageSerial"] = True
        self.payload_body["autoGenerateSerial"] = None
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại")
            self.assertEqual(400, code)

    def test_passTaxCodeEmpty_400_taxCodeIsNotExist(self):
        self.payload_body["taxInCode"] = ""
        self.payload_body["taxOutCode"] = ""
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Mã thuế không tồn tại")
            self.assertEqual(400, code)

    def test_passCodeAndName_400_codeAndNameHaveExisted(self):
        self.payload_body["name"] = "Laptop Dell"
        self.payload_body["code"] = "DRA"
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual(body["message"], "Mã danh mục đã tồn tại trong hệ thống")

    def test_codeAndName_Valid(self):
        self.payload_body["name"] = "ACB"
        self.payload_body["code"] = "A"
        with patch('catalog.extensions.signals.category_created_signal.send') as mock_signal:
            mock_signal.return_value = None
            with logged_in_user(self.user):
                code, body = self.call_api(data=self.payload_body)
                self.assertEqual(200, code)

    def test_passUnitId_400_unitIdIsNotExist(self):
        self.payload_body["unitId"] = 100
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Đơn vị tính không tồn tại")

    def test_passAttributeSetId_400_attributeSetIdIsNotExist(self):
        self.payload_body["attributeSetId"] = 100
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Bộ thuộc tính không tồn tại")

    def test_passMasterCategoryId_400_masterCategoryIdIsNotExist(self):
        self.payload_body["masterCategoryId"] = 123
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Danh mục sản phẩm không tồn tại")

    def test_passInvalidCode_400_codeMustNotHaveSpecialCharacters(self):
        self.payload_body["code"] = "qwew ewé "
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(body["message"], "Mã danh mục chỉ chứa các kí tự a-z A-Z 0-9 - _ .")

    def test_missingTaxIn_TaxOut_UnitId_400_someFieldsAreMissing(self):
        self.payload_body.pop("taxInCode")
        self.payload_body.pop("taxOutCode")
        self.payload_body.pop("unitId")
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertIsNone(body["result"]["taxInCode"])
            self.assertIsNone(body["result"]["taxOutCode"])
            self.assertIsNone(body["result"]["unitId"])

            result = m.Category.query.get(body["result"]["id"])
            self.assertIsNone(result.tax_in_code)
            self.assertIsNone(result.tax_out_code)
            self.assertIsNone(result.unit_id)

    def test_passNone_taxIn_taxOut_unitId_400_mustNotBeNone(self):
        self.payload_body["taxInCode"] = None
        self.payload_body["taxOutCode"] = None
        self.payload_body["unitId"] = None
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)

            self.assertIsNone(body["result"]["taxInCode"])
            self.assertIsNone(body["result"]["taxOutCode"])
            self.assertIsNone(body["result"]["unitId"])

            result = m.Category.query.get(body["result"]["id"])
            self.assertIsNone(result.tax_in_code)
            self.assertIsNone(result.tax_out_code)
            self.assertIsNone(result.unit_id)

    def test_passSameCategoryDataFromOtherSeller_200_successfully(self):
        category = self.categories[0]
        self.payload_body.update({
            'parentId': 0,
            'name': category.name,
            'code': category.code,
        })

        other_seller = fake.seller()
        other_user = fake.iam_user(seller_id=other_seller.id)
        with logged_in_user(other_user):
            code, body = self.call_api(data=self.payload_body)

        self.assertEqual(code, 200, body)

    def test_400_shippingTypeIsNotExist(self):
        self.payload_body['shippingTypes'] = [self.shipping_types[0].id, 123]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

    def test_200_shippingTypeIsAnEmptyList(self):
        self.payload_body['shippingTypes'] = []

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)

    def test_200_missingShippingType(self):
        del self.payload_body['shippingTypes']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)

    def test_200_ShippingTypesFieldIsNull(self):
        self.payload_body['shippingTypes'] = None

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)

    def test_400_shippingTypeIsInactive(self):
        inactive_shipping_type = fake.shipping_type(is_active=0)
        self.payload_body['shippingTypes'] = [self.shipping_types[0].id, inactive_shipping_type.id]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

    def test_400_parentDepthMoreThan6(self):
        with logged_in_user(self.user):
            self.payload_body['parentId'] = 16
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Không thể tạo danh mục con cho danh mục có độ sâu >= 6')

    def test_400_return_error_when_parent_category_has_product(self):
        with logged_in_user(self.user):
            parent_id = self.categories[0].id
            # parent has product
            fake.product_category(category_id=parent_id)
            self.payload_body['parentId'] = parent_id
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Không thể tạo danh mục con cho danh mục đã có sản phẩm')


class CategoriesWithSameNameTestCase(CreateCategoryTreeSetup):
    ISSUE_KEY = 'CATALOGUE-685'

    def update_category_url(self, category_id):
        return f'/categories/{category_id}'

    def setUp(self):
        super().setUp()
        self.category_update_signal_patcher = patch('catalog.extensions.signals.ram_category_updated_signal.send')
        self.mock_update_signal = self.category_update_signal_patcher.start()
        self.category_create_signal_patcher = patch('catalog.extensions.signals.ram_category_created_signal.send')
        self.mock_create_signal = self.category_create_signal_patcher.start()

    def tearDown(self):
        self.category_update_signal_patcher.stop()
        self.category_create_signal_patcher.stop()
        super().tearDown()

    def test_create2Categories_SameParentSameName__return_400_BadRequestWithMessage(self):
        self.payload_body['name'] = self.categories[1].name
        self.payload_body['parentId'] = self.categories[1].parent_id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual('Tên danh mục cùng danh mục cha đã tồn tại trong hệ thống', body['message'])

    def test_create2Categories_SameGrandParentSameName__return_200_CreateSuccessfully(self):
        self.payload_body['name'] = self.categories[8].name
        self.payload_body['parentId'] = self.categories[2].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)
            self.assertEqual(self.categories[8].name, body['result']['name'])
            self.assertEqual(self.categories[2].id, body['result']['parent']['id'])

    def test_create2Categories_DifferentBranchesSameName__return_200_CreateSuccessfully(self):
        self.payload_body['name'] = self.categories[8].name
        self.payload_body['parentId'] = self.categories[4].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)
            self.assertEqual(self.categories[8].name, body['result']['name'])
            self.assertEqual(self.categories[4].id, body['result']['parent']['id'])

    def test_create2Categories_ChildAndParentSameName__return_200_CreateSuccessfully(self):
        self.payload_body['name'] = self.categories[1].name
        self.payload_body['parentId'] = self.categories[1].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code)
            self.assertEqual(self.categories[1].name, body['result']['name'])
            self.assertEqual(self.categories[1].id, body['result']['parent']['id'])

    def test_updateCategory_SameParentSameName__return_400_BadRequestWithMessage(self):
        update_object = self.categories[2]
        self.payload_body['name'] = self.categories[1].name
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, method='PATCH',
                                       url=self.update_category_url(update_object.id))
            self.assertEqual(400, code)
            self.assertEqual('Tên danh mục cùng danh mục cha đã tồn tại trong hệ thống', body['message'])

    def test_updateCategories_SameGrandParentSameName__return_200_UpdateSuccessfully(self):
        update_object = self.categories[6]
        self.payload_body['name'] = self.categories[8].name
        self.payload_body['parentId'] = self.categories[2].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, method='PATCH',
                                       url=self.update_category_url(update_object.id))
            self.assertEqual(200, code)
            self.assertEqual(self.categories[8].name, body['result']['name'])
            self.assertEqual(self.categories[2].id, body['result']['parent']['id'])

    def test_updateCategory_DifferentBranchesSameName__return_200_UpdateSuccessfully(self):
        update_object = self.categories[6]
        self.payload_body['name'] = self.categories[1].name
        self.payload_body['parentId'] = self.categories[6].parent_id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, method='PATCH',
                                       url=self.update_category_url(update_object.id))
            self.assertEqual(200, code)
            self.assertEqual(self.categories[1].name, body['result']['name'])
            self.assertEqual(self.categories[6].parent_id, body['result']['parent']['id'])

    def test_updateCategory_ChildAndParentSameName__return_200_UpdateSuccessfully(self):
        update_object = self.categories[8]
        self.payload_body['name'] = self.categories[1].name
        self.payload_body['parentId'] = self.categories[1].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, method='PATCH',
                                       url=self.update_category_url(update_object.id))
            self.assertEqual(200, code)
            self.assertEqual(self.categories[1].name, body['result']['name'])
            self.assertEqual(self.categories[1].id, body['result']['parent']['id'])


class CategoriesDuplicatedNameTestCase(CreateCategoryTreeSetup):
    ISSUE_KEY = 'CATALOGUE-716'

    def update_category_url(self, category_id):
        return f'/categories/{category_id}'

    def setUp(self):
        super().setUp()
        self.category_update_signal_patcher = patch('catalog.extensions.signals.ram_category_updated_signal.send')
        self.mock_update_signal = self.category_update_signal_patcher.start()
        self.category_create_signal_patcher = patch('catalog.extensions.signals.ram_category_created_signal.send')
        self.mock_create_signal = self.category_create_signal_patcher.start()

    def tearDown(self):
        self.category_update_signal_patcher.stop()
        self.category_create_signal_patcher.stop()
        super().tearDown()

    def test_create2Categories_SameParentSameName_isActiveEqualTrue__return_400_BadRequestWithMessage(self):
        self.payload_body['name'] = self.categories[1].name
        self.payload_body['parentId'] = self.categories[1].parent_id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(400, code)
            self.assertEqual('Tên danh mục cùng danh mục cha đã tồn tại trong hệ thống', body['message'])

    def test_create2Categories_SameParentSameName_isActiveEqualFalse__return_200_CreateCategorySuccesfully(self):
        self.payload_body['name'] = self.categories[13].name
        self.payload_body['parentId'] = self.categories[4].id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(200, code, body)
            self.assertEqual(self.categories[13].name, body['result']['name'])
            self.assertEqual(self.categories[4].id, body['result']['parent']['id'])


class CreateCategoryWithAttributeSetTestCase(CreateCategoryTreeSetup):
    ISSUE_KEY = 'CATALOGUE-1351'

    def test_create_level_1_category_failed_without_attribute_set_id(self):
        del self.payload_body['masterCategoryId']
        del self.payload_body['attributeSetId']
        self.payload_body.update({'parentId': 0})

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 400)
            self.assertEqual(body['message'], 'Thông tin nhóm sản phẩm là bắt buộc nếu không có thông tin danh mục cha')

    def test_create_level_1_category_successfully_with_attribute_set_id(self):
        self.payload_body.update({'parentId': 0})
        del self.payload_body['masterCategoryId']

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], "Tạo mới danh mục thành công")

    def test_create_high_level_category_successfully_without_attribute_set_id(self):
        del self.payload_body['masterCategoryId']
        del self.payload_body['attributeSetId']
        self.payload_body.update({'parentId': 2})

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], f'Tạo mới danh mục thành công. Danh mục sẽ thừa hưởng bộ thuộc tính '
                                              f'{self.attribute_set.name} của danh mục cha: {self.categories[0].name}')

    def test_create_high_level_category_successfully_with_attribute_set_id(self):
        del self.payload_body['masterCategoryId']
        self.payload_body.update({'parentId': 2})

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Tạo mới danh mục thành công')


class TestCreateCategoryWithIsAdult(CreateCategoryTreeSetup):
    ISSUE_KEY = 'CATALOGUE-1532'

    def test_create_successfully_with_isAdult_is_true_200(self):
        self.payload_body.update({'isAdult': True})
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Tạo mới danh mục thành công')
            category = models.Category.query.get(body['result']['id'])
            self.assertTrue(category.is_adult)

    def test_create_successfully_with_isAdult_is_false_200(self):
        self.payload_body.update({'isAdult': False})

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Tạo mới danh mục thành công')
            category = models.Category.query.get(body['result']['id'])
            self.assertFalse(category.is_adult)

    def test_create_successfully_missing_isAdult_200(self):
        if 'isAdult' in self.payload_body:
            del self.payload_body['isAdult']
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Tạo mới danh mục thành công')
            category = models.Category.query.get(body['result']['id'])
            self.assertFalse(category.is_adult)

    def test_create_error_with_isAdult_is_not_boolean_400(self):
        self.payload_body.update({'isAdult': random.choice([fake.integer(), fake.text(), None, ''])})
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body)
            self.assertEqual(code, 400)
