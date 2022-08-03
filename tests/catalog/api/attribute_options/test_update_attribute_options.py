import json

from mock import patch
from tests import logged_in_user
from tests.faker import fake
from tests.catalog.api import APITestCaseWithMysql
from catalog import models as m
from catalog.constants import RAM_QUEUE


class UpdateAttributeOptionTestCase(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-1065'
    FOLDER = '/AttributeOptions/Update'

    def setUp(self):
        m.db.session.execute('truncate table ram_events')
        self.user = fake.iam_user()

        self.attribute = fake.attribute(value_type='selection')
        self.option = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id
        )
        self.option2 = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id
        )

        self.data = {
            'value': fake.text(),
        }

        self.patcher = patch('catalog.extensions.signals.unit_updated_signal.send')
        self.mock_signal = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def url(self, attribute_id, option_id):
        return f'/attributes/{attribute_id}/options/{option_id}'

    def method(self):
        return 'PATCH'

    def assertAttributeOption(self, option, json):
        assert option.value == json['value']

    def __assert_ram(self, option):
        ram_events = [r for r in m.db.session.execute('select * from ram_events order by id desc limit 1')]
        self.assertEqual(1, len(ram_events))
        ram_event = ram_events[0]
        payload_str = ram_event["payload"]
        payload = json.loads(payload_str)
        self.assertEqual(option.id, int(ram_event["ref"]))
        self.assertEqual(payload['attribute_id'], option.attribute_id)
        self.assertEqual(payload['attribute_option_id'], option.id)
        self.assertEqual(RAM_QUEUE.RAM_DEFAULT_PARENT_KEY, ram_event["parent_key"])
        self.assertEqual(RAM_QUEUE.RAM_UPDATE_ATTRIBUTE_KEY, ram_event["key"])

    def test_success(self):
        url = self.url(self.attribute.id, self.option.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body
        self.assertAttributeOption(self.option, self.data)
        self.__assert_ram(self.option)

        other_user = fake.iam_user(seller_id=2)
        other_option = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=other_user.seller_id
        )
        url = self.url(self.attribute.id, other_option.id)
        with logged_in_user(other_user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body
        self.assertAttributeOption(other_option, self.data)
        self.__assert_ram(other_option)

    def test_success_without_change(self):
        url = self.url(self.attribute.id, self.option.id)
        data = {'value': self.option.value}
        with logged_in_user(self.user):
            code, body = self.call_api(data, url=url)

        assert code == 200, body
        self.assertAttributeOption(self.option, data)
        ram_events = [r for r in m.db.session.execute('select * from ram_events order by id desc limit 1')]
        self.assertEqual(0, len(ram_events))

    def test_option_not_found(self):
        url = self.url(self.attribute.id, 69)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)
            assert code == 400

        other_option = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=69
        )
        url = self.url(self.attribute.id, other_option.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)
            assert code == 400

    def test_duplicate_value(self):
        url = self.url(self.attribute.id, self.option.id)
        self.data['value'] = self.option2.value.lower()

        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400

    def test_duplicate_value_of_other_attribute(self):
        attribute = fake.attribute(value_type='selection')
        fake.attribute_option(
            value=self.data['value'],
            seller_id=self.user.seller_id,
            attribute_id=attribute.id,
        )

        url = self.url(self.attribute.id, self.option.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body

    def test_return400_duplicateValueAfterTrimmingAndLowercase(self):
        fake.attribute_option(
            value='Vàng đồng',
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id
        )
        self.data['value'] = ' VÀNG    ĐỒNG  '
        url = self.url(self.attribute.id, self.option.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400, body
        assert body['message'] == 'Tùy chọn đã tồn tại'
