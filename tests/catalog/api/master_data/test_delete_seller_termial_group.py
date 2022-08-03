from catalog import models as m
from tests.faker import fake
from tests.catalog.api import APITestCase

_author_ = 'Nam.Vh'


class TestDeleteSellerTerminalGroup(APITestCase):
    def url(self):
        return '/master-data/seller_terminal_groups'

    def method(self):
        return 'DELETE'

    def test_delete_success(self):
        seller_terminal_group = fake.seller_terminal_group()
        data = {
            "id":seller_terminal_group.id,
            "sellerId":seller_terminal_group.seller_id,
            "terminalGroupId":seller_terminal_group.terminal_group_id,
            "isRequestedApproval":True,
            "createdAt":"2020-07-20T09:51:17",
            "updatedAt":"2020-07-20T09:51:17"
        }
        code, _ = self.call_api(data=data)
        assert code == 200
        assert m.SellerTerminalGroup.query.get(data['id']) is None
