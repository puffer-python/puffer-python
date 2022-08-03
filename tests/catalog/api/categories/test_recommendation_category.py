import json

from catalog import models
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetCategoryRecommendationSetup(APITestCase):
    def url(self):
        return '/categories/recommendation{}'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()

        self.master_categories_level_0 = fake.master_category(
            name='Mỹ phẩm - Làm đẹp', is_active=True,
            parent_id=0, seller_id=self.seller.id, attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_1 = fake.master_category(
            name='Chăm sóc tóc', is_active=True,
            parent_id=self.master_categories_level_0.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_2 = fake.master_category(
            name='Dầu gội, dầu xả', is_active=True,
            parent_id=self.master_categories_level_1.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )
        self.master_categories_level_3 = fake.master_category(
            name='Dầu Gội', is_active=True,
            parent_id=self.master_categories_level_2.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )


class GetCategoryRecommendation(GetCategoryRecommendationSetup):
    ISSUE_KEY = 'CATALOGUE-276'
    FOLDER = '/Category/Recommendation'

    def test_200_successfully(self):
        name = 'Dầu Gấc'
        limit = 2
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name={name}&limit={limit}'))

            self.assertEqual(code, 200)

            result = body.get('result')
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].get('id'), self.master_categories_level_3.id)
            self.assertEqual(result[0].get('path'), self.master_categories_level_3.path)
            self.assertEqual(result[0].get('fullPath'), "Mỹ phẩm - Làm đẹp / Chăm sóc tóc / Dầu gội, dầu xả / Dầu Gội")

            self.assertIsNotNone(result[0].get('attributeSet'))
            self.assertEqual(result[0].get('attributeSet').get('id'), self.attribute_set.id)
            self.assertEqual(result[0].get('attributeSet').get('name'), self.attribute_set.name)

    def test_passLimitExceedTheNumberOfMasterCategories_200(self):
        name = ''
        limit = 10
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name={name}&limit={limit}'))
            self.assertEqual(code, 200)

            result = body.get('result')
            self.assertEqual(len(result), 4)

    def test_inactiveMasterCategory_200(self):
        name = 'Dầu Gấc'
        limit = 10

        self.master_categories_level_3 = fake.master_category(
            name='Dầu Gấc', is_active=False,
            parent_id=self.master_categories_level_3.id, seller_id=self.seller.id,
            attribute_set_id=self.attribute_set.id
        )

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name={name}&limit={limit}'))
            self.assertEqual(code, 200)

            result = body.get('result')
            self.assertEqual(len(result), 4)

    def test_notPassName_400_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?limit=1'))
            self.assertEqual(code, 400)

    def test_400_NameTooLong(self):
        name = ''.join(['a' for _ in range(300)])

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name={name}'))
            self.assertEqual(code, 400)

    def test_400_limitTooLarge(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name=&limit=1000'))
            self.assertEqual(code, 400)


class RequestLogging(GetCategoryRecommendationSetup):
    ISSUE_KEY = 'CATALOGUE-508'
    FOLDER = '/Category/Recommendation'

    def headers(self):
        return {
            'X-USER-ID': self.user.seller_id
        }

    def test_200(self):
        category = fake.category(name='Dầu Gấc')
        name = category.name
        limit = 4
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(f'?name={name}&limit={limit}'))
            self.assertEqual(code, 200)

            result = models.RequestLog.query.all()
            self.assertEqual(len(result), 1)

            result = result[0]
            self.assertEqual(result.request_method, 'GET')
            self.assertEqual(result.request_path, f'/categories/recommendation')
            self.assertIsNotNone(json.loads(result.request_params))
            self.assertIsNone(result.request_body)
            self.assertIsNotNone(result.request_ip)
            self.assertIsNotNone(result.request_host)
            self.assertIsNotNone(result.response_body)
            self.assertEqual(result.created_by, str(self.user.seller_id))

