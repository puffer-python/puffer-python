import logging
import random

from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'Nam.Vh'
_logger_ = logging.getLogger(__name__)


class TestCreateSellerTerminal(APITestCase):
    ISSUE_KEY = 'SC-338'

    def url(self):
        return '/master-data/sellers-terminals'

    def method(self):
        return 'POST'

    def setUp(self):
        self.data = {
            'id': fake.integer(),
            'sellerId': fake.integer(),
            'terminalId': fake.integer(),
            'isOwner': random.choice([True, False]),
            'isRequestedApproval': random.choice([True, False]),
        }

    def test_passValidData_returnCreateSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['sellerId'], terminal_res['sellerId'])
        self.assertEqual(self.data['terminalId'], terminal_res['terminalId'])
        self.assertEqual(body['message'], 'Tạo mới seller terminal thành công')

    def test_passMissingBooleanValidData_returnCreateSuccess(self):
        """

        :return:
        """
        self.data.pop('isOwner')
        self.data.pop('isRequestedApproval')

        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(self.data['sellerId'], terminal_res['sellerId'])
        self.assertEqual(self.data['terminalId'], terminal_res['terminalId'])
        self.assertFalse(terminal_res['isOwner'])
        self.assertFalse(terminal_res['isRequestedApproval'])
        self.assertEqual(body['message'], 'Tạo mới seller terminal thành công')

    def test_missingTerminalId__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('terminalId')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_missingSellerId__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('sellerId')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def tearDown(self):
        pass


class TestUpdateSellerTerminal(APITestCase):
    ISSUE_KEY = 'SC-338'

    def url(self):
        return '/master-data/sellers-terminals'

    def method(self):
        return 'POST'

    def setUp(self):
        self.seller_terminal = fake.seller_terminal()

        self.data = {
            'id': self.seller_terminal.id,
            'sellerId': self.seller_terminal.seller_id,
            'terminalId': self.seller_terminal.terminal_id,
            'isOwner': random.choice([True, False]),
            'isRequestedApproval': random.choice([True, False]),
        }

    def test_passValidData_withExistedTerminal__returnUpdateSuccess(self):
        """

        :return:
        """

        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])

        self.assertEqual(body['message'], 'Cập nhật seller terminal thành công')

    def test_passMissingBooleanValidData_withExistedTerminal__returnUpdateSuccess(self):
        """

        :return:
        """
        self.data.pop('isOwner')
        self.data.pop('isRequestedApproval')
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertFalse(terminal_res['isOwner'])
        self.assertFalse(terminal_res['isRequestedApproval'])
        self.assertEqual(body['message'], 'Cập nhật seller terminal thành công')

    def test_wrongCode_withExistedTerminal__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['terminalId'] = 0
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_wrongsellerId_withExistedTerminal__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['sellerId'] = 0
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def tearDown(self):
        pass
