import logging
from unittest.mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'phuong.h'
_logger_ = logging.getLogger(__name__)


class TestCreateUnit(APITestCase):
    ISSUE_KEY = 'CATALOGUE-664'
    FOLDER = '/Unit/Create'

    def url(self):
        return '/units'

    def method(self):
        return 'POST'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.unit_created_signal.send')
        self.mock_signal = self.patcher.start()

        self.uom_attribute = fake.attribute(code='uom')

        self.data = {
            'name': fake.text(255),
            'code': fake.text(30),
            'displayName': fake.text(255)
        }
        self.user = fake.iam_user()

    def tearDown(self):
        self.patcher.stop()

    def add_trim_data(self):
        return {
            'name': '  ' + self.data['name'],
            'code': self.data['code'] + '  ',
            'displayName': '  ' + self.data['displayName']
        }

    def assert_create_unit_success(self, res):
        """

        :param res:
        :return:
        """
        unit_res = res['result']
        self.assertEqual(self.data['name'], unit_res['name'], 'match name in response')
        self.assertEqual(self.data['code'], unit_res['code'], 'match code in response')
        self.assertEqual(self.data['displayName'], unit_res['displayName'], 'match displayName in response')
        self.mock_signal.assert_called_once()

        unit = models.Unit.query.filter(models.Unit.id == unit_res['id']).first()

        self.assertEqual(self.data['name'], unit.name, 'match name')
        self.assertEqual(self.data['code'], unit.code, 'match code')
        self.assertEqual(self.data['displayName'], unit.display_name, 'match display_name')
        self.assertEqual(self.user.seller_id, unit.seller_id)

        attribute_options = models.AttributeOption.query.filter(
            models.AttributeOption.attribute_id == self.uom_attribute.id,
            models.AttributeOption.code == unit.code,
            models.AttributeOption.seller_id == unit.seller_id).all()
        self.assertEqual(1, len(attribute_options), 'only 1 attribute option')
        attribute_option = attribute_options[0]
        self.assertEqual(attribute_option.value, unit.name, 'match value in attribute_option')
        self.assertEqual(attribute_option.display_value, unit.display_name, 'match display_name in attribute_option')
        self.assertEqual(attribute_option.seller_id, unit.seller_id, 'match seller_id in attribute_option')

    def test_return200__Success_empty_unit(self):
        """

        :return:
        """
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_create_unit_success(body)

    def test_return200__Success_has_unit_same_code_at_other_seller(self):
        """

        :return:
        """
        fake.unit(code=self.data['code'], seller_id=self.user.seller_id + 1)
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_create_unit_success(body)

    def test_return200__Success_has_unit_same_name_at_other_seller(self):
        """

        :return:
        """
        fake.unit(name=self.data['name'], seller_id=self.user.seller_id + 1)
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_create_unit_success(body)

    def test_return200__Success_already_has_data_in_attribute_option(self):
        """

        :return:
        """
        fake.attribute_option(attribute_id=self.uom_attribute.id,
                              seller_id=self.user.seller_id,
                              code=self.data['code'])
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_create_unit_success(body)

    def assert_fail(self, data, message):
        code, body = self.call_api_with_login(data=data)
        self.assertEqual(400, code)
        self.assertEqual(message, body.get('message'))
        self.mock_signal.assert_not_called()

    def test_return400__empty_name(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': '',
            'code': 'code1',
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__empty_code(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
            'code': '',
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__name_length_over_255(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': fake.text(256),
            'code': 'code1',
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__code_length_over_30(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
            'code': fake.text(31),
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__display_name_length_over_255(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
            'code': 'code1',
            'displayName': fake.text(256)
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__duplicate_name(self):
        """

        :return:
        """
        name = fake.text(255)
        fake.unit(name=name, seller_id=self.user.seller_id)
        self.assert_fail(data={
            'name': name,
            'code': 'code1',
            'displayName': 'displayName1'
        }, message='Tên đơn vị tính đã tồn tại')

    def test_return400__duplicate_code(self):
        """

        :return:
        """
        code = fake.text(30)
        fake.unit(code=code, seller_id=self.user.seller_id)
        self.assert_fail(data={
            'name': 'name1',
            'code': code,
            'displayName': 'displayName1'
        }, message='Mã đơn vị tính đã tồn tại')

    def test_return400__special_character_in_code(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
            'code': '*code',
            'displayName': 'displayName1'
        }, message='Mã đơn vị không được nhập ký tự đặc biệt, hoặc tiếng việt có dấu')

    def test_return400__vietnamese_character_in_code(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
            'code': 'cốt',
            'displayName': 'displayName1'
        }, message='Mã đơn vị không được nhập ký tự đặc biệt, hoặc tiếng việt có dấu')




