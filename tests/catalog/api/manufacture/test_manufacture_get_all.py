# coding=utf-8
import json
import logging
import random

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.models import MANUFACTURE_CODE

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class TestManufactureGetAll(APITestCase):

    def setUp(self):
        self.manufacture_attribute = fake.attribute(code=MANUFACTURE_CODE, value_type='selection')
        self.manufactures = [fake.attribute_option(attribute_id=self.manufacture_attribute.id) for _ in range(10)]

    def method(self):
        return 'GET'

    def url(self):
        return '/manufactures'

    def test_success_api(self):
        code, body = self.call_api(url=self.url(), method=self.method())
        self.assertEqual(len(body.get('result')), len(self.manufactures) + 1)
        result_manufacture = random.choice(body.get('result'))
        self.assertIsNotNone(result_manufacture.get('id'))
        from catalog.models.attribute_option import AttributeOption
        manufacture = AttributeOption.query.get(result_manufacture.get('id'))
        self.assertEqual(result_manufacture.get('code'), manufacture.code)
        self.assertEqual(result_manufacture.get('name'), manufacture.value)

    def test_empty_data(self):
        self.manufacture_attribute.code = fake.text()
        from catalog.models import db
        db.session.commit()
        code, body = self.call_api(url=self.url(), method=self.method())
        self.assertEqual(code, 200)
        self.assertListEqual(body.get('result'), [])
