# coding=utf-8
import logging
import random
from tests.faker import fake
from tests.catalog.api import APITestCase
from catalog import models as m

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class TestCreateAttribute(APITestCase):

    def url(self):
        return '/attributes'

    def method(self):
        return 'POST'

    def setUp(self):
        self.data = {
            'name': fake.name(),
            'displayName': fake.name(),
            'code': fake.text(),
            'valueType': random.choice(('text', 'selection', 'multiple_select')),
            'isSystem': random.choice((True, False)),
        }

    def test_create_attribute_with_is_system_bool(self):
        url = self.url()
        is_system = random.choice((True, False))
        self.data['isSystem'] = is_system
        code, body = self.call_api(self.data, url=url)
        assert code == 200, body
        assert body.get('result').get('isSystem') == is_system
        attribute = m.Attribute.query.get(body.get('result').get('id'))
        assert attribute.is_system == is_system

    def test_create_attribute_without_is_system(self):
        url = self.url()
        self.data.pop('isSystem')
        code, body = self.call_api(self.data, url=url)
        assert code == 200, body
        assert body.get('result').get('isSystem') == False

    def test_create_attribute_and_is_system_none(self):
        url = self.url()
        self.data['isSystem'] = None
        code, body = self.call_api(self.data, url=url)
        assert code == 400, body
