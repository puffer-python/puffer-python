import logging

from catalog import models
from tests.catalog.api import APITestCase, APITestCaseWithMysql
from tests.faker import fake

_author_ = 'phuong.h'
_logger_ = logging.getLogger(__name__)


class TestGetUnits(APITestCase):
    ISSUE_KEY = 'CATALOGUE-663'
    FOLDER = '/Unit/Get'

    def url(self):
        return '/units'

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        self.units_by_name = [fake.unit(name='name {}'.format(i), seller_id=self.user.id) for i in range(2)]
        self.units_by_code = [fake.unit(code='code {}'.format(i)) for i in range(2)]
        self.units_of_other_seller = [fake.unit(name='name {}'.format(i + 10),
                                                code='code {}'.format(i + 10),
                                                seller_id=self.user.id + 1) for i in range(5)]

    def assert_get_unit_success(self, res, units):
        units = sorted(units, key=lambda x: x.id)

        for i in range(len(res)):
            self.assertEqual(res[i].get('id'), units[i].id)
            self.assertEqual(res[i].get('name'), units[i].name)
            self.assertEqual(res[i].get('code'), units[i].code)

    def test_return200__passQuery(self):
        url = self.url() + '?page=1&pageSize=3&query=e'
        code, body = self.call_api_with_login(url=url)

        self.assertEqual(200, code)
        result = body['result']

        self.assertEqual(result['totalRecords'], 4)
        self.assertEqual(result['currentPage'], 1)
        self.assertEqual(result['pageSize'], 3)

        result = body['result']['units']
        self.assertEqual(len(result), 3)

        self.assert_get_unit_success(result, self.units_by_name + self.units_by_code)

    def test_return200__passEmpty(self):
        code, body = self.call_api_with_login(url=self.url())

        self.assertEqual(200, code)
        result = body['result']

        self.assertEqual(result['totalRecords'], 4)
        self.assertEqual(result['currentPage'], 1)
        self.assertEqual(result['pageSize'], 10)

        result = body['result']['units']
        self.assertEqual(len(result), 4)

        self.assert_get_unit_success(result, self.units_by_name + self.units_by_code)

    def test_return200__passNameKeywords(self):
        url = self.url() + '?query=  NAME'
        code, body = self.call_api_with_login(url=url)

        self.assertEqual(200, code)
        result = body['result']

        self.assertEqual(result['totalRecords'], 2)
        self.assertEqual(result['currentPage'], 1)
        self.assertEqual(result['pageSize'], 10)

        result = body['result']['units']
        self.assertEqual(len(result), 2)

        self.assert_get_unit_success(result, self.units_by_name)

    def test_return200__passCodeKeywords(self):
        url = self.url() + '?query= Code'
        code, body = self.call_api_with_login(url=url)

        self.assertEqual(200, code)
        result = body['result']

        self.assertEqual(result['totalRecords'], 2)
        self.assertEqual(result['currentPage'], 1)
        self.assertEqual(result['pageSize'], 10)

        result = body['result']['units']
        self.assertEqual(len(result), 2)

        self.assert_get_unit_success(result, self.units_by_code)

    def test_return200__passPageSizeAndPageLargeThanCurrentData(self):
        url = self.url() + '?page=3&pageSize=3'
        code, body = self.call_api_with_login(url=url)

        self.assertEqual(200, code)
        result = body['result']

        self.assertEqual(result['totalRecords'], 4)
        self.assertEqual(result['currentPage'], 3)
        self.assertEqual(result['pageSize'], 3)

        result = body['result']['units']
        self.assertEqual(len(result), 0)

    def test_return400__passPageSize0(self):
        url = self.url() + '?page=1&pageSize=0'
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

        url = self.url() + '?page=0&query=naMe'
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

    def test_return400__passPageSizeTooLarge(self):
        url = self.url() + '?page=1&pageSize=42949672951&name=naMe&code=Code'
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

        url = self.url() + '?page=42949672951&name=naMe&code=Code'
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

        url = self.url() + f'?page=0&query={"".join(["n" for _ in range(1000)])}'
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

    def test_return400__passPageNull(self):
        url = self.url() + '?page='
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)

        url = self.url() + '?pageSize='
        code, body = self.call_api_with_login(url=url)
        self.assertEqual(code, 400)


class TestUnitCaseSensitive(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-577'
    FOLDER = '/Unit/Get'

    def url(self):
        return '/units'

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        self.units_by_name = fake.unit(name='Bó')

    def test_passValidParams__returnGetSuccess(self):
        url = self.url() + '?page=1&pageSize=3&query=bo'
        code, body = self.call_api_with_login(url=url)

        self.assertEqual(200, code)
        result = body['result']['units']
        self.assertEqual(len(result), 1)
