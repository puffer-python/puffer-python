#coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake


class GetDetailMasterCategoryTestCase(APITestCase):
    ISSUE_KEY = 'SC-661'

    def url(self):
        return '/master_categories/{}'

    def method(self):
        return 'GET'

    def test_passIdInvalid__returnBadRequest(self):
        category_id = fake.random_int(100, 1000)
        code, body = self.call_api(url=self.url().format(category_id))
        assert 400 == code
        assert 'INVALID' == body['code']
        assert 'Danh mục không tồn tại' == body['message']

    def test_passIdValid__returnCategory(self):
        category = fake.master_category(
            parent_id=fake.master_category().id
        )
        code, body = self.call_api(url=self.url().format(category.id))
        assert 200 == code
        assert 'SUCCESS' == body['code']

        cat_json = body['result']
        assert cat_json['name'] == category.name
        assert cat_json['code'] == category.code
        assert cat_json['taxInCode'] == category.tax_in_code
        assert cat_json['manageSerial'] == category.manage_serial
        assert cat_json['autoGenerateSerial'] == category.auto_generate_serial
        assert cat_json['attributeSet']['id'] == category.attribute_set_id
        assert cat_json['parent']['id'] == category.parent_id
        assert cat_json['root']['id'] == category.root.id
