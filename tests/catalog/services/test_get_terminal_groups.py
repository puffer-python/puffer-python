#coding=utf-8

from unittest import TestCase
from mock import patch
import requests
from catalog.services.terminal import get_terminal_groups


class TestGetTerminalGroup(TestCase):
    def test_success(self):
        with patch('requests.get') as mock_get:
            resp = requests.Response()
            resp.status_code = 200
            resp._content = b'''
            {
                "result": {
                    "terminalGroups": [{
                        "sellerID": 1,
                        "description": "",
                        "id": 57,
                        "isOwner": 1,
                        "code": "AUTOTEST_SELLING_TERMINAL_GROUP",
                        "type": "SELL",
                        "sellerName": "",
                        "isActive": 1,
                        "name": "AUTOTEST_SELLING_TERMINAL_GROUP"
                    }],
                  "total": 1,
                  "page": 1,
                  "pageSize": 1
                }
            }
            '''
            mock_get.return_value = resp
            ret = get_terminal_groups(1)
            assert isinstance(ret, list)
            assert len(ret) == 1, resp.json()

    def test_fail(self):
        with patch('requests.get') as mock_get:
            resp = requests.Response()
            resp.status_code = 400
            mock_get.return_value = resp
            ret = get_terminal_groups(1)
            assert isinstance(ret, list)
            assert len(ret) == 0
