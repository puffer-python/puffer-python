from catalog import models
from tests.catalog.api import APITestCase, APITestCaseWithMysql
from tests.faker import fake
from catalog.utils import camel_case


class GetMasterCategoryListTestCase(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-238'
    FOLDER = '/MasterCategory/List'

    def setUp(self):
        categories = [fake.master_category() for _ in range(10)]

    def url(self):
        return '/master_categories'

    def method(self):
        return 'GET'

    def assertCategory(self, category, json):
        simple_key = ('id', 'name', 'code', 'is_active', 'depth',
                      'path', 'image', 'tax_in_code', 'tax_out_code',
                      'manage_serial', 'auto_generate_serial')

        for key in simple_key:
            assert getattr(category, key) == json.get(camel_case(key))

    def assertCategories(self, categories, list_json):
        pairs = zip(
            sorted(categories, key=lambda x: x.id),
            sorted(list_json, key=lambda x: x['id']),
        )
        for obj, json in pairs:
            self.assertCategory(obj, json)

    def test_filter_by_is_active(self):

        # is_active = true
        url = self.url() + '?pageSize=1000&isActive=true'
        code, body = self.call_api(url=url)
        self.categories = models.MasterCategory.query.all()

        assert code == 200
        self.assertCategories(filter(lambda x: x.is_active, self.categories), body['result']['masterCategories'])

        # is_active = false
        url = self.url() + '?pageSize=1000&isActive=false'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(filter(lambda x: not x.is_active, self.categories), body['result']['masterCategories'])

        # not filter is_active
        url = self.url() + '?pageSize=1000'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(self.categories, body['result']['masterCategories'])

    def test_filterByCode__shouldReturnAllMatchedCategories(self):
        sample_codes = ['abcdef', 'abcdefg']
        new_categories = [fake.master_category(code=code) for code in sample_codes]
        url = self.url() + '?query=abcdef'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])

    def test_filterByCodeNotMatching__shouldReturnEmptyList(self):
        url = self.url() + '?query=kdzvdlc'
        code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['masterCategories'] == []

    def test_filterByName__shouldReturnAllMatchedCategories(self):
        sample_codes = ['category 1', 'categoryyy 2']
        new_categories = [fake.master_category(name=name) for name in sample_codes]
        url = self.url() + '?query=category'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])

    def test_filterByNameNotMatching__shouldReturnEmptyList(self):
        url = self.url() + '?query=kdzvdlc'
        code, body = self.call_api(url=url)

        assert code == 200
        assert body['result']['masterCategories'] == []


class GetMasterCategoryListByVietnameseTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-396'
    FOLDER = '/MasterCategory/List/Vietnamese'

    def setUp(self):
        self.categories = [fake.master_category(name=f'name{i}') for i in range(10)]

    def url(self):
        return '/master_categories'

    def method(self):
        return 'GET'

    def assertCategory(self, category, json):
        simple_key = ('id', 'name', 'code', 'is_active', 'depth',
                      'path', 'image', 'tax_in_code', 'tax_out_code',
                      'manage_serial', 'auto_generate_serial')

        for key in simple_key:
            assert getattr(category, key) == json.get(camel_case(key))

    def assertCategories(self, categories, list_json):
        pairs = zip(
            sorted(categories, key=lambda x: x.id),
            sorted(list_json, key=lambda x: x['id']),
        )
        for obj, json in pairs:
            self.assertCategory(obj, json)

    def test_filter_by_name__shouldReturnMatchedCategoryWithUnicodeBuiltIn(self):
        # Use unicode to hop, vni, viqr
        sample_names = ['củ', 'củ', 'củ']
        new_categories = [fake.master_category(name=name) for name in sample_names]
        url = self.url() + '?query=củ'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])

    def test_filter_by_name__shouldReturnMatchedCategoryWithUnicodeCombinatorial(self):
        # Use unicode dung san, vni, viqr
        sample_names = ['củ', 'củ', 'củ']
        new_categories = [fake.master_category(name=name) for name in sample_names]
        url = self.url() + '?query=củ'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])

    def test_filter_by_name__shouldReturnMatchedCategoryWithVNI(self):
        # Use unicode dung san, to hop, vnqr
        sample_names = ['củ', 'củ', 'củ']
        new_categories = [fake.master_category(name=name) for name in sample_names]
        url = self.url() + '?query=củ'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])

    def test_filter_by_name__shouldReturnMatchedCategoryWithVIQR(self):
        # Use unicode dung san, to hop, vni
        sample_names = ['củ', 'củ', 'củ']
        new_categories = [fake.master_category(name=name) for name in sample_names]
        url = self.url() + '?query=củ'
        code, body = self.call_api(url=url)

        assert code == 200
        self.assertCategories(new_categories, body['result']['masterCategories'])
