# coding=utf-8
import logging

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import models as m

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class TestGetAttribute(APITestCase):
    def setUp(self):
        self.attribute = fake.attribute()

    def url(self):
        return '/attributes/{}'.format(self.attribute.id)

    def method(self):
        return 'GET'

    def test_get_attribute_check_is_system(self):
        url = self.url()
        code, body = self.call_api(url=url)
        assert code == 200, body
        attribute = m.Attribute.query.get(self.attribute.id)
        assert body.get('result').get('isSystem') == attribute.is_system
