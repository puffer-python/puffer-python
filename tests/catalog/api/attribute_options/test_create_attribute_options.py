from mock import patch
from tests import logged_in_user
from tests.faker import fake
from tests.catalog.api import APITestCase, APITestCaseWithMysql
from catalog.models import AttributeOption


class CreateAttributeOptionTestCase(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-1065'
    FOLDER = '/AttributeOptions/Create'

    def setUp(self):
        self.user = fake.iam_user()

        self.attribute = fake.attribute(value_type='selection')
        self.option = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id,
        )

        self.data = {
            'code': fake.unique_str(),
            'value': fake.text(),
        }

    def url(self, attribute_id):
        return f'/attributes/{attribute_id}/options'

    def method(self):
        return 'POST'

    @patch('catalog.services.seller.get_seller_by_id')
    def test_success(self, get_seller_mocker):
        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }
        url = self.url(self.attribute.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body

        option = AttributeOption.query.get(body['result']['id'])

        assert option is not None
        assert option.value == self.data['value']
        assert option.code == self.data['code']
        assert option.seller_id == self.user.seller_id
        assert option.attribute_id == self.attribute.id

        # other user creates a new option with same data
        other_user = fake.iam_user(seller_id=2)
        with logged_in_user(other_user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body

    def test_duplicate_value(self):
        url = self.url(self.attribute.id)
        self.data['value'] = self.option.value.lower()

        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400

    def test_duplicate_code(self):
        url = self.url(self.attribute.id)
        self.data['code'] = self.option.code.lower()

        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400

    @patch('catalog.services.seller.get_seller_by_id')
    def test_duplicate_value_of_other_attribute(self, get_seller_mocker):
        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }
        attribute = fake.attribute(value_type='selection')
        fake.attribute_option(
            value=self.data['value'],
            code=self.data['code'],
            seller_id=self.user.seller_id,
            attribute_id=attribute.id,
        )

        url = self.url(self.attribute.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 200, body

    def test_create_unicode_for_code(self):
        self.data['code'] = 'Tét-fail'
        url = self.url(self.attribute.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400, body

    @patch('catalog.services.seller.get_seller_by_id')
    def test_restrict_service_package_with_uom_attribute(self, get_seller_mocker):
        get_seller_mocker.return_value = {
            'servicePackage': 'NOT_FBS',
        }
        attribute = fake.attribute(value_type='selection', code='uom')
        url = self.url(attribute.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400
        assert body['message'] == 'Seller này không thể tạo được tuỳ chọn do đang sử dụng gói dịch vụ NOT_FBS'
        self.patcher = patch('catalog.extensions.signals.unit_created_signal.send')

    @patch('catalog.services.seller.get_seller_by_id')
    def test_return400_duplicatedAfterTrimmingAndLowercase(self, get_seller_mocker):
        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }
        fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id,
            value='Vàng đồng'
        )
        self.data['value'] = ' VÀNG    ĐỒNG  '

        url = self.url(self.attribute.id)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data, url=url)

        assert code == 400, body
        assert body['message'] == 'Tùy chọn đã tồn tại'
