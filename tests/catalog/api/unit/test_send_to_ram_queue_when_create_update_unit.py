# coding=utf-8
import json
import logging
from unittest.mock import patch

from catalog.models import db
from catalog.services.categories import CategoryService
from tests.catalog import RAM_QUEUE
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake

__author__ = 'phuong.h'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class SendToRamQueueWhenCreateUpdateUnitTestCase(APITestCaseWithMysql):

    ISSUE_KEY = 'CATALOGUE-678'
    FOLDER = '/Unit/SendToRamQueue'

    def url(self):
        return '/units'

    def method(self):
        return 'POST'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.uom_attribute = fake.attribute(code='uom')

    @staticmethod
    def random_payload_body():
        return {
            "code": fake.text(4),
            "name": fake.text(10)
        }

    def assert_saveEventToQueueWhenCreate(self):
        payload_request = self.random_payload_body()
        code, body = self.call_api_with_login(data=payload_request, url=self.url(), method=self.method())
        self.assertEqual(code, 200, body)
        ram_events = [r for r in db.session.execute('select * from ram_events order by id desc limit 1')]
        self.assertEqual(1, len(ram_events))
        ram_event = ram_events[0]
        self.assertEqual(str(body["result"]["id"]), ram_event["ref"])
        payload_str = ram_event["payload"]
        payload = json.loads(payload_str)
        self.assertEqual(body["result"]["id"], payload["id"])
        self.assertEqual(RAM_QUEUE.RAM_DEFAULT_PARENT_KEY, ram_event["parent_key"])
        self.assertEqual(RAM_QUEUE.RAM_INSERT_UNIT_KEY, ram_event["key"])

    def assert_saveEventToQueueWhenUpdate(self):
        db.session.execute('truncate table ram_events')
        unit = fake.unit()
        url = '/units/{}'.format(unit.id)
        code, body = self.call_api_with_login(data={
            "name": fake.text(10)
        }, url=url, method="PATCH")
        self.assertEqual(code, 200, body)

        ram_events = [r for r in db.session.execute('select * from ram_events')]
        ram_event = ram_events[0]
        self.assert_match_update(ram_event, unit)

    def assert_match_update(self, ram_event, unit):
        self.assertEqual(str(unit.id), ram_event["ref"])
        payload_str = ram_event["payload"]
        payload = json.loads(payload_str)
        self.assertEqual(unit.id, payload["id"])
        self.assertEqual(RAM_QUEUE.RAM_DEFAULT_PARENT_KEY, ram_event["parent_key"])
        self.assertEqual(RAM_QUEUE.RAM_UPDATE_UNIT_KEY, ram_event["key"])

    def test_200_create_send1Request_save1EventToQueue(self):
        self.assert_saveEventToQueueWhenCreate()

    def test_200_create_sendMultiRequest_saveMultiEventToQueue(self):
        for _ in range(5):
            self.assert_saveEventToQueueWhenCreate()

    def test_200_update_send1Request_save1EventToQueue(self):
        self.assert_saveEventToQueueWhenUpdate()

    def test_200_update_sendMultiRequest_saveMultiEventToQueue(self):
        for _ in range(5):
            self.assert_saveEventToQueueWhenUpdate()

    def test_200_create_send1Request_send1EventToConnectorQueue(self):
        pass

    def test_200_create_sendMultiRequest_sendMultiEventToConnector(self):
        pass

    def test_200_update_send1Request_send1EventToConnector(self):
        pass

    def test_200_update_sendMultiRequest_sendMultiEventToConnector(self):
        pass
