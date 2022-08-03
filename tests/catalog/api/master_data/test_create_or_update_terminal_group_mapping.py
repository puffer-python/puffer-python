from catalog import models as m
from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'Nam.Vh'


class TestCreateTerminalGroupMapping(APITestCase):
    def url(self):
        return '/master-data/terminal_group_mapping'

    def method(self):
        return 'POST'

    def setUp(self):
        self.terminal_group = fake.terminal_group()
        self.terminal = fake.terminal()

    def test_create_success(self):
        data = {
            "op_type": "upsert",
            "terminal_groups": [{
                "id": 1,
                "terminal": {
                    "code": self.terminal.code
                },
                "group": {
                    "code": self.terminal_group.code,
                    "type": self.terminal_group.type,
                }
            }]
        }
        code, _ = self.call_api(data=data)
        assert code == 200

    def test_delete(self):
        mapping = fake.terminal_group_mapping()
        id = mapping.id
        data = {
            "op_type": "delete",
            "terminal_groups": [{
                "id": id,
            }]
        }
        code, _ = self.call_api(data=data)
        assert code == 200, _
        assert m.TerminalGroupTerminal.query.get(id) is None
