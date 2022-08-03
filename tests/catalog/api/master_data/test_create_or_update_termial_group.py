from catalog import models as m
from tests.catalog.api import APITestCase

_author_ = 'Nam.Vh'


class TestCreateTerminalGroup(APITestCase):
    def url(self):
        return '/master-data/terminal_groups'

    def method(self):
        return 'POST'

    def test_create_success(self):
        data = {
            "id": 59,
            "code": "GOO_PRICE_0001",
            "name": "Root Biz",
            "type": "SELL",
            "sellerId": 10,
            "isActive": True,
            "createdAt": "2020-07-09T08:33:53",
            "updatedAt": "2020-07-27T08:44:44"
        }
        code, _ = self.call_api(data=data)
        assert code == 200
        obj = m.TerminalGroup.query.filter(
            m.TerminalGroup.code == data['code']
        ).first()
        assert obj.name == data['name']
        assert obj.code == data['code']
