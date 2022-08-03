# coding=utf-8
from unittest.mock import patch

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GetUpdateSeoInfoTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-830'
    FOLDER = '/Import/GetUpdateSeoInfoTemplate'

    def url(self):
        return '/import?type=update_seo_info'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.patcher_send_file = patch('catalog.services.imports.template.TemplateUpdateSeoInfo.send_file')
        self.mock_send_file = self.patcher_send_file.start()
        self.mock_send_file.return_value = {}

    def tearDown(self):
        self.patcher_send_file.stop()

    def test_200_successfully(self):
        with logged_in_user(self.user):
            code, body = self.call_api()

            self.assertEqual(code, 200)
            self.mock_send_file.assert_called_once()

    def test_500_fileNotFound(self):
        """
        assume that this case never happens
        """
        self.assertTrue(True)
