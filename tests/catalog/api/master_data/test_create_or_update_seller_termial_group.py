from catalog import models as m
from tests.catalog.api import APITestCase

_author_ = 'Nam.Vh'


class TestCreateSellerTerminalGroup(APITestCase):
    def url(self):
        return '/master-data/seller_terminal_groups'

    def method(self):
        return 'POST'

    def test_create_success(self):
        data = {
            "id":55,
            "sellerId":22,
            "terminalGroupId":56,
            "isRequestedApproval":True,
            "createdAt":"2020-07-20T09:51:17",
            "updatedAt":"2020-07-20T09:51:17"
        }
        code, _ = self.call_api(data=data)
        assert code == 200
        obj = m.SellerTerminalGroup.query.get(data['id'])
        assert obj.seller_id == data['sellerId']
        assert obj.terminal_group_id == data['terminalGroupId']
