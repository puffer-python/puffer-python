#coding=utf-8
from unittest.mock import patch

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetCreateProductBasicInfoTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-656'
    FOLDER = '/Import/GetUpdateImagesSkusTemplate'

    def url(self):
        return '/import?type=update_images_skus'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

    def tearDown(self):
        pass

    def test_return200__Success_Matching_File(self):
        code, body = self.call_api_with_login()
        self.assert_import_template_file('template_import_update_images_skus_v3.0.xlsx', body)
        self.assertEqual(code, 200)
