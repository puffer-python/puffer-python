import datetime
import logging
import random

from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'Nam.Vh'
_logger_ = logging.getLogger(__name__)


class TestCreateTerminal(APITestCase):
    ISSUE_KEY = 'SC-338'

    def url(self):
        return '/master-data/terminals'

    def method(self):
        return 'POST'

    def setUp(self):
        self.data = {
            'id': fake.integer(),
            'name': fake.name(),
            'code': fake.text(),
            'wardCode': fake.text(),
            'sellerId': 1,
            'type': fake.text(),
            'platform': fake.text(),
            'fullAddress': fake.text(),
            'isActive': random.choice([True, False]),
            'isRequestedApproval': random.choice([True, False]),
            'updatedAt': fake.datetime(format='%Y-%m-%dT%H:%M:%S')
        }

    def test_passMissingBoolean_ValidData_withNoTerminal__returnCreateSuccess(self):
        """

        :return:
        """
        self.data.pop('isActive')
        self.data.pop('isRequestedApproval')
        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['code'], terminal_res['code'])
        self.assertFalse(terminal_res['isActive'])
        self.assertFalse(terminal_res['isRequestedApproval'])
        self.assertEqual(body['message'], 'Tạo mới terminal thành công')

    def test_passValidData_withNoTerminal__returnCreateSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['code'], terminal_res['code'])
        self.assertEqual(body['message'], 'Tạo mới terminal thành công')

    def test_passEmptyData__returnInvalidResponse(self):
        """

        :return:
        """
        code, body = self.call_api(data={
            "name": "",
            "code": "",
        })
        self.assertEqual(400, code)

    def test_missingName__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('name')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_missingsellerId__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('sellerId')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_missingCode__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('code')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def tearDown(self):
        pass


class TestUpdateTerminal(APITestCase):
    ISSUE_KEY = 'SC-338'

    def url(self):
        return '/master-data/terminals'

    def method(self):
        return 'POST'

    def setUp(self):
        updated_at = datetime.datetime(2019, 1, 1, 0, 0, 0)
        self.terminal = fake.terminal(updated_at=updated_at)
        self.data = {
            'id': self.terminal.id,
            'name': fake.name(),
            'code': self.terminal.code,
            'sellerId': self.terminal.seller_id,
            'type': fake.text(),
            'platform': fake.text(),
            'wardCode': fake.text(),
            'fullAddress': fake.text(),
            'isActive': random.choice([True, False]),
            'isRequestedApproval': random.choice([True, False]),
            'updatedAt': datetime.datetime(2020, 1, 1, 0, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")
        }

    def test_passValidData_withExistedTerminal__returnUpdateSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['name'], terminal_res['name'])
        self.assertEqual(self.data['isRequestedApproval'], terminal_res['isRequestedApproval'])
        self.assertEqual(self.data['isActive'], terminal_res['isActive'])
        self.assertEqual(body['message'], 'Cập nhật terminal thành công')

    def test_passMissingBooleanValidData_withExistedTerminal__returnUpdateSuccess(self):
        """

        :return:
        """
        self.data.pop('isActive')
        self.data.pop('isRequestedApproval')
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['name'], terminal_res['name'])
        self.assertFalse(terminal_res['isRequestedApproval'])
        self.assertFalse(terminal_res['isActive'])
        self.assertEqual(body['message'], 'Cập nhật terminal thành công')

    def test_wrongCode_withExistedTerminal__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['code'] = fake.unique_str(8).lower()
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def tearDown(self):
        pass
