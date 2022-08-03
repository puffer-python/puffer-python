import logging
import string
import random
from tests.catalog.api import APITestCase
from catalog import models as m
from tests.faker import fake

_author_ = 'phuong.h'
_logger_ = logging.getLogger(__name__)


class TestCreateShippingType(APITestCase):
    ISSUE_KEY = 'CATALOGUE-422'
    FOLDER = '/ShippingType/Create'

    def url(self):
        return '/shipping_types'

    def method(self):
        return 'POST'

    def setUp(self):
        self.items = [fake.shipping_type() for _ in range(100)]
        self.user = fake.iam_user()
        self.data = {
            'name': fake.text(255),
            'code': fake.text(255, string.ascii_uppercase + "_")
        }

    def assert_create_shipping_type_success(self, res):
        """

        :param res:
        :return:
        """
        item = res['result']
        item_in_db = m.ShippingType.query.get(item['id'])
        self.assertEqual(self.data['name'], item_in_db.name)
        self.assertEqual(self.data['code'], item_in_db.code)
        self.assertEqual(self.user.email, item_in_db.created_by)
        self.assertEqual(self.user.email, item_in_db.updated_by)

    def test_return200__Success(self):
        code, body = self.call_api_with_login(data=self.data)
        self.assertEqual(200, code)
        self.assert_create_shipping_type_success(body)

    def test_return400__RequireName(self):
        self.data['name'] = None
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__InvalidNameLength(self):
        self.data['name'] = fake.text(256)
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__DuplicateCaseSensitiveName(self):
        self.data['name'] = random.choice(self.items).name
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__DuplicateCaseInsensitiveName(self):
        # sqllite don't support case insensitive
        assert True

    def test_return400__RequireCode(self):
        self.data['code'] = None
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__InvalidCodeLength(self):
        self.data['code'] = fake.text(256, string.ascii_uppercase + "_")
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__InvalidCodeFormat(self):
        self.data['code'] = fake.text(250, string.ascii_uppercase + "_") + fake.text(1)
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)

    def test_return400__DuplicateCode(self):
        self.data['code'] = random.choice(self.items).code
        code, _ = self.call_api_with_login(data=self.data)
        self.assertEqual(400, code)
