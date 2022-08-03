# coding=utf-8
import logging
import random
from tests.faker import fake
from tests.catalog.api import APITestCase
from catalog import models as m

__author__ = 'Dung.HT'
_logger = logging.getLogger(__name__)


class TestUpdateAttribute(APITestCase):

    def url(self):
        return '/attributes/{}'.format(self.attribute.id)

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.attribute = fake.attribute()
        self.data = {
            'name': fake.name(),
            'displayName': fake.name(),
            'code': fake.text(),
            'valueType': random.choice(('text', 'selection', 'multiple_select')),
            'isSystem': random.choice((True, False)),
        }

    def test_update_attribute_with_is_system_bool(self):
        url = self.url()
        is_system = random.choice((True, False))
        self.data['isSystem'] = is_system
        code, body = self.call_api(self.data, url=url)
        assert code == 200, body
        assert body.get('result').get('isSystem') == is_system
        attribute = m.Attribute.query.get(self.attribute.id)
        assert attribute.is_system == is_system

    def test_update_attribute_without_is_system(self):
        url = self.url()
        self.data.pop('isSystem')
        code, body = self.call_api(self.data, url=url)
        assert code == 200, body
        assert body.get('result').get('isSystem') == self.attribute.is_system

    def test_update_attribute_and_is_system_none(self):
        url = self.url()
        self.data['isSystem'] = None
        code, body = self.call_api(self.data, url=url)
        assert code == 400, body
