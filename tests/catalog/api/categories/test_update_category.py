# coding=utf-8

import json
import logging
from mock import patch
from catalog import models as m, models
import config

from catalog.services.categories import CategoryService
from catalog.constants import CATEGORY_MAX_DEPTH
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'quang.da'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class SetupUpdateCategory(APITestCase):
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
        self.payload_body = {
            "code": "DAQ",
            "name": "DAAQ",
            "parentId": 8,
            "manageSerial": True,
            "autoGenerateSerial": True,
            "attributeSetId": self.attribute_set.id,
            "unitId": self.unit.id,
            "taxInCode": self.tax_in_code.code,
            "taxOutCode": self.tax_out_code.code
        }

        self.patcher_signal = patch('catalog.extensions.signals.ram_category_updated_signal.send')
        self.mock_signal = self.patcher_signal.start()

    def tearDown(self):
        self.patcher_signal.stop()

    def url(self, obj_id):
        return '/categories/{}'.format(obj_id)

    def method(self):
        return 'PATCH'

    def assertBody(self, payload_body, obj_dict):
        for key, value in payload_body.items():
            if key == 'parentId':
                assert obj_dict['parent']['id'] == value
            elif key == 'attributeSetId':
                assert obj_dict['attributeSet']['id'] == value
            else:
                assert obj_dict.get(key) == value


class UpdateCategoryTreeTestCase(SetupUpdateCategory):
    ISSUE_KEY = 'CATALOGUE-351'

    def test_update_category_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertBody(self.payload_body, body["result"])

    def test_objId_inValid(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(100))
            assert code == 400
            assert body["message"] == "Danh mục 100 không tồn tại"

    def test_parentId_inValid(self):
        with logged_in_user(self.user):
            self.payload_body["parentId"] = 100
            code, body = self.call_api(data=self.payload_body, url=self.url(8))
            assert code == 400
            assert body["message"] == "Danh mục 100 không tồn tại"

    def test_parentId_inValid2(self):
        with logged_in_user(self.user):
            self.payload_body["parentId"] = 7
            code, body = self.call_api(data=self.payload_body, url=self.url(7))
            assert code == 400
            assert body["message"] == "Danh mục cha không phù hợp"

    def test_parentId_inValid3(self):
        with logged_in_user(self.user):
            # Current data:
            # ```
            # >>> path
            # "1/3"
            # ```
            # Update product id 1 to have id 3 as its parent should fail
            self.payload_body["parentId"] = 3
            code, body = self.call_api(data=self.payload_body, url=self.url(1))
            assert code == 400
            assert body["message"] == "Không thể cài đặt một danh mục đang thuộc chính nó làm danh mục cha"

    def test_parentId_inValid4(self):
        with logged_in_user(self.user):
            # Current data:
            # ```
            # >>> path
            # "1/2/9/12/15/16"
            # ```
            # Update product id 1 to have id 15 as its parent should fail
            self.payload_body["parentId"] = 15
            code, body = self.call_api(data=self.payload_body, url=self.url(1))
            assert code == 400
            assert body["message"] == "Không thể cài đặt một danh mục đang thuộc chính nó làm danh mục cha"

    def test_nameAndCode_existence(self):
        self.payload_body["name"] = "Laptop Dell"
        self.payload_body["code"] = "DRA"
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(400, code)
            self.assertEqual(body["message"], "Mã danh mục đã tồn tại trong hệ thống")

    def test_codeAndName_Valid(self):
        self.payload_body["name"] = "ABC"
        self.payload_body["code"] = "A"
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(200, code)

    def test_send_manageSerial_nonValid(self):
        self.payload_body["manageSerial"] = False
        self.payload_body["autoGenerateSerial"] = None
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại")
            self.assertEqual(400, code)

    def test_send_manageSerial_nonValid2(self):
        self.payload_body["serialGenerationSource"] = "none"
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại")
            self.assertEqual(400, code)

    def test_not_send_manageSerial(self):
        self.payload_body.pop("autoGenerateSerial")
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(200, code)

    def test_inActive_activeNode(self):
        self.payload_body["isActive"] = False
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Không thể vô hiệu danh mục có danh mục đang hoạt động")
            self.assertEqual(400, code)

    def test_move_inActiveNode(self):
        self.payload_body["parentId"] = 7
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(11))
            self.assertEqual(body["message"], "Không thể chuyển danh mục hiệu lực sang danh mục vô hiệu")
            self.assertEqual(400, code)

    def test_unitId_notValid(self):
        self.payload_body["unitId"] = 100
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Đơn vị tính không tồn tại")

    def test_attributeSetId_notValid(self):
        self.payload_body["attributeSetId"] = 100
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Bộ thuộc tính không tồn tại")

    def test_attributeSetId_isNone(self):
        self.payload_body.pop("attributeSetId")
        # bypass the maximal depth test
        self.payload_body["parentId"] = 2
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["result"]["attributeSet"], None)

    def test_code_inValid(self):
        self.payload_body["code"] = "qwewewé "
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(body["message"], "Mã danh mục chỉ chứa các kí tự a-z A-Z 0-9 - _ .")

    def test_passNotExistedMasterCategoryId__returnBadRequest(self):
        self.payload_body = {
            "masterCategoryId": 123
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 400)
            self.mock_signal.assert_not_called()

    def test_passAInactiveMasterCategoryId__returnBadRequest(self):
        master_category = fake.master_category(is_active=False)
        self.payload_body = {
            "masterCategoryId": master_category.id,
            "attributeSetId": self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), "Danh mục sản phẩm không tồn tại")
            self.mock_signal.assert_not_called()

    def test_passNone__taxIn_taxOut__returnSuccessfull(self):
        self.payload_body = {
            "taxInCode": None,
            "taxOutCode": None,
            "unitId": None,
            "attributeSetId": self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 200)
            self.mock_signal.assert_called_once()

            result = m.Category.query.get(9)
            self.assertIsNone(result.tax_in_code)
            self.assertIsNone(result.tax_out_code)
            self.assertIsNone(result.unit_id)

    def test_duplicate_category_without_same_seller(self):
        category = self.categories[0]
        self.payload_body = {
            'name': category.name,
            'code': category.code,
            'attributeSetId': self.attribute_set.id,
        }

        other_seller = fake.seller()
        other_user = fake.iam_user(seller_id=other_seller.id)
        other_category = fake.category(seller_id=other_seller.id)

        with logged_in_user(other_user):
            code, body = self.call_api(data=self.payload_body, url=self.url(other_category.id))
            self.assertEqual(code, 200, body)
            self.mock_signal.assert_called_once()

            self.assertEqual(self.payload_body['name'], other_category.name)
            self.assertEqual(self.payload_body['code'], other_category.code)

    def test_updated_category_depth(self):
        with logged_in_user(self.user):
            # id = 6, path = 4/6
            self.payload_body["parentId"] = 6
            # id = 1, path (longest) = 1/2/9/12/15/16
            code, body = self.call_api(data=self.payload_body, url=self.url(1))

            assert code == 400
            assert body["message"] == f"Không cho phép cập nhật danh mục có độ sâu > {CATEGORY_MAX_DEPTH}"


class UpdateMasterCategoryForCategory(SetupUpdateCategory):
    ISSUE_KEY = 'CATALOGUE-508'
    FOLDER = '/Category/updateCategory'

    def setUp(self):
        super().setUp()
        self.master_category_level_1 = fake.master_category(is_active=True)
        self.master_category_level_2 = fake.master_category(parent_id=self.master_category_level_1.id, is_active=True)
        self.category = fake.category(is_active=True, seller_id=self.seller.id,
                                      master_category_id=self.master_category_level_2.id)

    def test_passTheRootMasterCategoryId_200_returnSuccessfully(self):
        category = fake.category(is_active=True, seller_id=self.seller.id)

        self.payload_body = {
            "masterCategoryId": self.master_category_level_2.id,
            "attributeSetId": self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(category.id))
            self.assertEqual(code, 200)

            self.assertTrue('masterCategory' in body['result'])
            result_master_category = body.get('result').get('masterCategory')
            self.assertEqual(result_master_category.get('id'), self.master_category_level_2.id)
            self.assertEqual(result_master_category.get('path'), self.master_category_level_2.path)

            self.mock_signal.assert_called_once()

            category = m.Category.query.get(category.id)
            self.assertEqual(category.master_category_id, self.master_category_level_2.id)

    def test_notPassMasterCategory_200_returnSuccessfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(code, 200)

            self.assertTrue('masterCategory' in body['result'])
            result_master_category = body.get('result').get('masterCategory')
            self.assertEqual(result_master_category.get('id'), self.master_category_level_2.id)
            self.assertEqual(result_master_category.get('path'), self.master_category_level_2.path)

            self.mock_signal.assert_called_once()

    def test_passNoneMasterCategory_200_returnSuccessfully(self):
        self.payload_body = {
            'masterCategoryId': None,
            "attributeSetId": self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(code, 200)

            self.assertTrue('masterCategory' in body['result'])
            self.assertIsNone(body.get('result').get('masterCategory'))
            self.mock_signal.assert_called_once()

    def test_passNotExistMasterCategory_400_returnBadRequest(self):
        self.payload_body = {
            'masterCategoryId': 123
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(code, 400)


class UpdateShippingTypesForCategory(SetupUpdateCategory):
    ISSUE_KEY = 'CATALOGUE-457'
    FOLDER = '/Category/update'

    def setUp(self):
        super().setUp()

        self.category = fake.category(is_active=1, seller_id=self.seller.id)
        self.shipping_type = fake.shipping_type()
        fake.category_shipping_type(
            self.category.id,
            self.shipping_type.id
        )

    def test_200_validShippingTypes(self):
        shipping_types = [fake.shipping_type() for _ in range(2)]
        self.payload_body = {
            'shippingTypes': [x.id for x in shipping_types],
            'attributeSetId': self.attribute_set.id
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(200, code)

            category_shipping_types = models.CategoryShippingType.query.all()
            self.assertEqual(len(category_shipping_types), 2)
            for sellable_shipping_type in category_shipping_types:
                self.assertIn(sellable_shipping_type.shipping_type_id, self.payload_body['shippingTypes'])

    def test_200_deleteCurrentShippingTypeWhenInputtingAnEmptyList(self):
        self.payload_body = {
            'shippingTypes': [],
            'attributeSetId': self.attribute_set.id
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(200, code)

            category_shipping_types = models.CategoryShippingType.query.all()
            self.assertEqual(len(category_shipping_types), 0)

    def test_400_notExistShippingTypes(self):
        self.payload_body = {
            'shippingTypes': [123],
            'attributeSetId': self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

            category_shipping_types = models.CategoryShippingType.query.all()
            self.assertEqual(len(category_shipping_types), 1)
            self.assertEqual(category_shipping_types[0].shipping_type_id, self.shipping_type.id)

    def test_400_inactiveShippingTypes(self):
        shipping_types = [fake.shipping_type(), fake.shipping_type(is_active=0)]
        self.payload_body = {
            'shippingTypes': [x.id for x in shipping_types],
            'attributeSetId': self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

            category_shipping_types = models.CategoryShippingType.query.all()
            self.assertEqual(len(category_shipping_types), 1)
            self.assertEqual(category_shipping_types[0].shipping_type_id, self.shipping_type.id)

    def test_200_ShippingTypesFieldIsNull(self):
        self.payload_body = {
            'shippingTypes': None,
            'attributeSetId': self.attribute_set.id
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(self.category.id))
            self.assertEqual(200, code)

            category_shipping_types = models.CategoryShippingType.query.all()
            self.assertEqual(len(category_shipping_types), 1)
            self.assertEqual(category_shipping_types[0].shipping_type_id, self.shipping_type.id)


class TestDeactivateCategory(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1330'
    FOLDER = '/Category/UpdateCategory/Deactivate'

    def method(self):
        return 'PATCH'

    def url(self):
        return f'/categories/{self.category.id}'

    def setUp(self):
        self.created_by = 'quang.lm'
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        self.category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )
        self.category_update_signal_patcher = patch('catalog.extensions.signals.ram_category_updated_signal.send')
        self.mock_update_signal = self.category_update_signal_patcher.start()
        self.attribute_set = fake.attribute_set()

    def tearDown(self):
        self.category_update_signal_patcher.stop()

    def __add_product_category(self, category_id):
        product = fake.product(category_id=category_id,
                               master_category_id=self.master_category.id,
                               created_by=self.created_by)
        fake.product_category(product_id=product.id, category_id=category_id, created_by=self.created_by)

    def test_deactivate_category_return400_with_category_has_products(self):
        self.__add_product_category(self.category.id)
        payload = {'isActive': False}
        with logged_in_user(self.user):
            code, body = self.call_api(data=payload)
            self.assertEqual(400, code)
            self.assertEqual('Không vô hiệu được ngành hàng có sản phẩm', body['message'])

    def test_deactivate_category_return200_with_category_has_no_products(self):
        category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )
        category_id = category.id
        self.__add_product_category(category_id)
        payload = {
            'isActive': False,
            'attributeSetId': self.attribute_set.id
        }
        with logged_in_user(self.user):
            code, body = self.call_api(data=payload)
            updated_category = m.Category.query.get(self.category.id)
            self.assertEqual(200, code)
            self.assertEqual(False, updated_category.is_active)


class RequestLogging(SetupUpdateCategory):
    def headers(self):
        return {
            'X-USER-ID': self.user.seller_id
        }

    def test_200(self):
        category = fake.category(is_active=True, seller_id=self.seller.id)

        self.payload_body = {
            'masterCategoryId': fake.master_category(is_active=True).id,
            'attributeSetId': self.attribute_set.id
        }

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(category.id))
            self.assertEqual(code, 200)

            result = models.RequestLog.query.all()
            self.assertEqual(len(result), 1)

            result = result[0]
            self.assertEqual(result.request_method, 'PATCH')
            self.assertIn('/categories', result.request_path)
            self.assertIsNotNone(result.request_params)
            self.assertIsNotNone(json.dumps(result.request_body))
            self.assertIsNotNone(result.request_ip)
            self.assertIsNotNone(result.request_host)
            self.assertIsNotNone(result.response_body)
            self.assertEqual(result.created_by, str(self.user.seller_id))

class UpdateCategoryWithAttributeSetTestCase(SetupUpdateCategory):
    ISSUE_KEY = 'CATALOGUE-1351'

    def test_update_level_1_category_failed_without_attribute_set_id(self):
        del self.payload_body["attributeSetId"]
        self.payload_body.update({"parentId": 0})
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 400)
            self.assertEqual(body["message"], 'Thông tin nhóm sản phẩm là bắt buộc nếu không có thông tin danh mục cha')

    def test_update_level_1_category_successfully_with_attribute_set_id(self):
        self.payload_body.update({"parentId": 0})
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Cập nhập danh mục thành công')

    def test_update_high_level_category_successfully_without_attribute_set_id(self):
        self.payload_body.update({'parentId': 2})
        del self.payload_body['attributeSetId']
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], f'Cập nhập danh mục thành công. Danh mục sẽ thừa hưởng bộ thuộc tính '
                                              f'{self.attribute_set.name} của danh mục cha: {self.categories[0].name}')

    def test_update_high_level_category_successfully_with_attribute_set_id(self):
        self.payload_body.update({'parentId': 2})
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.payload_body, url=self.url(9))
            self.assertEqual(code, 200)
            self.assertEqual(body['message'], 'Cập nhập danh mục thành công')