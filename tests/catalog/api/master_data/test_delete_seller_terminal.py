import logging
import random

from catalog.models import SellerTerminal
from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'Nam.Vh'
_logger_ = logging.getLogger(__name__)


class TestCreateSellerTerminal(APITestCase):
    ISSUE_KEY = 'SC-338'

    def url(self):
        return '/master-data/sellers-terminals'

    def method(self):
        return 'DELETE'

    def setUp(self):
        self.seller_terminal = fake.seller_terminal()

        self.data = {
            'id': self.seller_terminal.id,
            'sellerId': self.seller_terminal.seller_id,
            'terminalId': self.seller_terminal.terminal_id,
            'isOwner': random.choice([True, False]),
            'isRequestedApproval': random.choice([True, False]),
        }

    def test_passValidData_returnDeleteSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)
        self.assertEqual(200, code)
        terminal_res = body['result']
        self.assertEqual(self.data['id'], terminal_res['id'])
        self.assertEqual(body['message'], 'Xóa seller terminal thành công')

        seller_terminal = SellerTerminal.query.filter(
            SellerTerminal.id == self.data['id']
        ).first()
        self.assertIsNone(seller_terminal)

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

    def test_wrongCode_withExistedTerminal__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['terminalId'] = 0
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_wrongSellerId_withExistedTerminal__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['sellerId'] = 0
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_wrongId__returnInvalidResponse(self):
        """

        :return:
        """
        self.data['id'] = 0
        code, body = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def tearDown(self):
        pass
