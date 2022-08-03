# coding=utf-8
import logging

from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class TestUpdateUnit(APITestCase):
    ISSUE_KEY = 'CATALOGUE-665'
    FOLDER = '/Unit/Update'

    PATH = '/units/{unit_id}'

    def url(self):
        return self.PATH.format(unit_id=self.unit.id)

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.unit_updated_signal.send')
        self.mock_signal = self.patcher.start()

        self.uom_attribute = fake.attribute(code='uom')

        self.user = fake.iam_user()
        self.unit = fake.unit(seller_id=self.user.seller_id)
        self.data = {
            'name': fake.text(255),
            'displayName': fake.text(255),
        }

    def tearDown(self):
        self.patcher.stop()

    def add_trim_data(self):
        return {
            'name': '  ' + self.data['name'],
            'displayName': '  ' + self.data['displayName']
        }

    def assert_update_unit_success(self, res):
        """

        :param res:
        :return:
        """
        unit_res = res['result']
        self.assertEqual(self.data['name'], unit_res['name'], 'match name in response')
        self.assertEqual(self.unit.code, unit_res['code'], 'match code in response')
        self.assertEqual(self.data['displayName'], unit_res['displayName'], 'match displayName in response')
        self.assertEqual(self.unit.seller_id, unit_res['sellerId'], 'match seller_id in response')
        self.mock_signal.assert_called_once()

        unit = models.Unit.query.filter(models.Unit.id == self.unit.id).first()

        self.assertEqual(self.data['name'], unit.name, 'match name')
        self.assertEqual(self.unit.code, unit.code, 'match code')
        self.assertEqual(self.data['displayName'], unit.display_name, 'match display_name')
        self.assertEqual(self.unit.seller_id, unit.seller_id)

        attribute_options = models.AttributeOption.query.filter(
            models.AttributeOption.attribute_id == self.uom_attribute.id,
            models.AttributeOption.code == unit.code,
            models.AttributeOption.seller_id == unit.seller_id).all()
        self.assertEqual(1, len(attribute_options), 'only 1 attribute option')
        attribute_option = attribute_options[0]
        self.assertEqual(attribute_option.value, unit.name, 'match value in attribute_option')
        self.assertEqual(attribute_option.display_value, unit.display_name, 'match display_name in attribute_option')
        self.assertEqual(attribute_option.seller_id, unit.seller_id, 'match seller_id in attribute_option')

    def test_return200__Success(self):
        """

        :return:
        """
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_update_unit_success(body)

    def test_return200__Success_seller_id_is_0(self):
        """

        :return:
        """
        self.unit.seller_id = 0
        models.db.session.commit()
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_update_unit_success(body)

    def test_return200__Success_already_has_data_in_attribute_option(self):
        """

        :return:
        """
        fake.attribute_option(attribute_id=self.uom_attribute.id,
                              seller_id=self.user.seller_id,
                              code=self.unit.code)
        code, body = self.call_api_with_login(data=self.add_trim_data())

        self.assertEqual(200, code)
        self.assert_update_unit_success(body)

    def assert_fail(self, data, message, url=None):
        code, body = self.call_api_with_login(data=data, url=url)
        self.assertEqual(400, code)
        self.assertEqual(message, body.get('message'))
        self.mock_signal.assert_not_called()

    def test_return400__empty_name(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': '',
            'displayName': 'displayName1',
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__name_length_over_255(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': fake.text(256),
            'displayName': 'displayName1'
        }, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại')

    def test_return400__display_name_length_over_255(self):
        """

        :return:
        """
        self.assert_fail(data={
            'name': 'name1',
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
            'displayName': 'displayName1'
        }, message='Tên đơn vị tính đã tồn tại')

    def test_return400__non_exists_id(self):
        self.assert_fail(url=self.PATH.format(unit_id=123), data=self.data,
                         message='Đơn vị tính không tồn tại hoặc bạn không có quyền sửa đơn vị tính này')

    def test_return400__exists_id_but_belong_to_other_seller(self):
        self.unit = fake.unit(seller_id=self.user.seller_id + 1)
        self.assert_fail(data=self.data,
                         message='Đơn vị tính không tồn tại hoặc bạn không có quyền sửa đơn vị tính này')

    def test_return404__invalid_id(self):
        code, body = self.call_api(url=self.PATH.format(unit_id='abc'), data=self.data)
        self.assertEqual(code, 404)
