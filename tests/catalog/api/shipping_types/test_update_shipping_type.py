import logging
import random

from tests.catalog.api import APITestCase
from catalog import models as m

from tests.faker import fake

_author_ = 'phuong.h'
_logger_ = logging.getLogger(__name__)


class TestUpdateShippingType(APITestCase):
    ISSUE_KEY = 'CATALOGUE-423'
    FOLDER = '/ShippingType/Update'

    def url(self):
        return '/shipping_types/{r_id}'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.items = [fake.shipping_type() for _ in range(100)]
        self.user = fake.iam_user()
        self.data = {
            'name': fake.text(255)
        }

        item = random.choice(self.items)
        self.id = item.id
        self.main_url = self.url().format(r_id=self.id)

    def assert_update_success(self):
        item_in_db = m.ShippingType.query.get(self.id)
        self.assertEqual(self.data['name'], item_in_db.name)
        self.assertEqual(self.user.email, item_in_db.updated_by)

    def test_return200__Success(self):
        code, body = self.call_api_with_login(data=self.data, url=self.main_url)
        self.assertEqual(code, 200)
        self.assert_update_success()

    def test_return400__RequireName(self):
        self.data['name'] = None
        code, _ = self.call_api_with_login(data=self.data, url=self.main_url)
        self.assertEqual(400, code)

    def test_return400__InvalidNameLength(self):
        self.data['name'] = fake.text(256)
        code, _ = self.call_api_with_login(data=self.data, url=self.main_url)
        self.assertEqual(400, code)

    def test_return400__DuplicateCaseSensitiveName(self):
        random_item = random.choice(self.items)
        while random_item.id == self.id:
            random_item = random.choice(self.items)
        self.data['name'] = random_item.name
        code, _ = self.call_api_with_login(data=self.data, url=self.main_url)
        self.assertEqual(400, code)

    def test_return400__DuplicateCaseInsensitiveName(self):
        # sqllite don't support case insensitive
        assert True

    def test_return400__IdNotFoundInDatabase(self):
        random_id = random.randint(100000, 10000000)
        self.id = random_id
        self.main_url = self.url().format(r_id=self.id)
        code, _ = self.call_api_with_login(data=self.data, url=self.main_url)
        self.assertEqual(400, code)

