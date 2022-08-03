from mock import patch
from tests import logged_in_user
from tests.faker import fake
from tests.catalog.api import APITestCase


class GetAttributeOptionListTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-278'

    def setUp(self):
        self.user = fake.iam_user()
        self.attribute = fake.attribute(value_type='selection')
        self.marketplace_options = [fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=0,
        ) for _ in range(5)]
        self.seller_options = [fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id
        ) for _ in range(5)]

    def url(self, attribute_id):
        return f'/attributes/{attribute_id}/options'

    def method(self):
        return 'GET'

    def assertListSellerUnit(self, options, list_json):
        assert len(options) == len(list_json)
        sorted_options = sorted(options, key=lambda x: x.id)
        sorted_json = sorted(list_json, key=lambda x: x['id'])
        for option, json in zip(sorted_options, sorted_json):
            assert option.code == json['code']
            assert option.value == json['value']

    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_ids_in_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }

        options = fake.random_elements(self.seller_options, 3, unique=True)
        url = self.url(self.attribute.id) + '?ids={}'.format(','.join([str(x.id) for x in options]))
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == len(options)
        self.assertListSellerUnit(options, body['result']['options'])

    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_codes_in_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }

        options = fake.random_elements(self.seller_options, 3, unique=True)
        url = self.url(self.attribute.id) + '?codes={}'.format(','.join([x.code for x in options]))
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == len(options)
        self.assertListSellerUnit(options, body['result']['options'])

    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_keyword_in_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBS',
        }

        option = self.seller_options[0]

        url = self.url(self.attribute.id) + '?keyword={}'.format(option.value[:5])
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == 1
        self.assertListSellerUnit([option], body['result']['options'])

    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_ids_in_not_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBE',
        }

        options = fake.random_elements(self.marketplace_options, 3, unique=True)
        url = self.url(self.attribute.id) + '?ids={}'.format(','.join([str(x.id) for x in options]))
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == len(options)
        self.assertListSellerUnit(options, body['result']['options'])


    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_codes_in_not_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBE',
        }

        options = fake.random_elements(self.marketplace_options, 3, unique=True)
        url = self.url(self.attribute.id) + '?codes={}'.format(','.join([x.code for x in options]))
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == len(options)
        self.assertListSellerUnit(options, body['result']['options'])

    @patch('catalog.services.seller.get_seller_by_id')
    def test_search_with_keyword_in_not_fbs_seller(self, get_seller_mocker):

        get_seller_mocker.return_value = {
            'servicePackage': 'FBE',
        }

        option = self.marketplace_options[0]

        url = self.url(self.attribute.id) + '?keyword={}'.format(option.value[:5])
        with logged_in_user(self.user):
            code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['totalRecords'] == 1
        self.assertListSellerUnit([option], body['result']['options'])
