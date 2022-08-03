# coding=utf-8
import json
import logging
from abc import ABC

import config
from catalog import models as m
from catalog.services.categories import CategoryService
from tests.catalog import RAM_QUEUE
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake
from tests import logged_in_user

__author__ = 'phuong.h'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class SendToRamQueueWhenCreateCategoryTestCase(APITestCaseWithMysql):

    ISSUE_KEY = 'CATALOGUE-550'
    FOLDER = '/Category/Create/SendToRamQueue'

    def url(self):
        return '/categories'

    def method(self):
        return 'POST'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.unit = fake.unit()
        self.tax_in_code = fake.tax(fake.text(4))
        self.tax_out_code = fake.tax(fake.text(4))
        self.shipping_types = [fake.shipping_type() for _ in range(2)]

    def random_payload_body(self):
        return {
            "code": fake.text(4),
            "name": fake.text(10),
            "parentId": 0,
            "manageSerial": True,
            "autoGenerateSerial": True,
            "unitId": self.unit.id,
            "taxInCode": self.tax_in_code.code,
            "taxOutCode": self.tax_out_code.code,
            "attributeSetId": self.attribute_set.id,
            "shippingTypes": [self.shipping_types[0].id, self.shipping_types[1].id],
        }

    def assert_saveEventToQueueWhenCreate(self):
        payload_request = self.random_payload_body()
        code, body = self.call_api_with_login(data=payload_request, url=self.url(), method=self.method())
        self.assertEqual(code, 200, body)
        ram_events = [r for r in m.db.session.execute('select * from ram_events order by id desc limit 1')]
        self.assertEqual(1, len(ram_events))
        ram_event = ram_events[0]
        self.assertEqual(str(body["result"]["id"]), ram_event["ref"])
        payload_str = ram_event["payload"]
        payload = json.loads(payload_str)
        self.assertEqual(body["result"]["id"], payload["id"])
        self.assertEqual(RAM_QUEUE.RAM_DEFAULT_PARENT_KEY, ram_event["parent_key"])
        self.assertEqual(RAM_QUEUE.RAM_INSERT_CATEGORY_KEY, ram_event["key"])

    def assert_saveEventToQueueWhenUpdate(self):
        category = fake.category(seller_id=self.seller.id)
        url = '/categories/{}'.format(category.id)
        code, body = self.call_api_with_login(data={
            "name": fake.text(10),
            "attributeSetId": self.attribute_set.id,
        }, url=url, method="PATCH")
        self.assertEqual(code, 200, body)
        ram_events = [r for r in m.db.session.execute('select * from ram_events order by id desc limit 1')]
        self.assertEqual(1, len(ram_events))
        ram_event = ram_events[0]
        self.assert_match_update(ram_event, category)

    def assert_match_update(self, ram_event, category):
        self.assertEqual(str(category.id), ram_event["ref"])
        payload_str = ram_event["payload"]
        payload = json.loads(payload_str)
        self.assertEqual(category.id, payload["id"])
        self.assertEqual(RAM_QUEUE.RAM_DEFAULT_PARENT_KEY, ram_event["parent_key"])
        self.assertEqual(RAM_QUEUE.RAM_UPDATE_CATEGORY_KEY, ram_event["key"])

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

    def test_200_update_send1Request_save2EventToQueue_WhenChangeParentIsChild(self):
        pass

    def test_200_create_send1Request_send1EventToConnectorQueue(self):
        pass

    def test_200_create_sendMultiRequest_sendMultiEventToConnector(self):
        pass

    def test_200_update_send1Request_send1EventToConnector(self):
        pass

    def test_200_update_sendMultiRequest_sendMultiEventToConnector(self):
        pass

    def test_200_update_send1Request_save2EventToConnector_WhenChangeParentIsChild(self):
        pass
