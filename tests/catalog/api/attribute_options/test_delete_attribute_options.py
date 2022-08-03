from mock import patch
from tests import logged_in_user
from tests.faker import fake
from tests.catalog.api import APITestCase


class DeleteAttributeOptionTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-278'

    def setUp(self):
        self.user = fake.iam_user()

        self.attribute = fake.attribute(value_type='selection')
        self.option = fake.attribute_option(
            seller_id=self.user.seller_id,
            attribute_id=self.attribute.id
        )

    def url(self, attribute_id, option_id):
        return f'/attributes/{attribute_id}/options/{option_id}'

    def method(self):
        return 'DELETE'

    def test_success(self):
        self.patcher = patch('catalog.extensions.signals.unit_deleted_signal.send')
        self.mock_signal = self.patcher.start()
        url = self.url(self.option.attribute_id, self.option.id)
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200, body

    def test_delete_unit_of_other_seller(self):
        other_option = fake.attribute_option(seller_id=2, attribute_id=self.attribute.id)
        url = self.url(self.attribute.id, other_option.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 400

    def test_delete_unit_not_exist(self):
        url = self.url(self.attribute.id, 69)

        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 400

    def test_delete_unit_was_used(self):
        sellable = fake.sellable_product(uom_code=self.option.code)

        url = self.url(self.attribute.id, self.option.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 400
