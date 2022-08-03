import pytest
from mock import patch

from catalog import models
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class CreateVariantImageAPITestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-120'

    def url(self):
        return '/variants/{}/external_images'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.iam_user = fake.iam_user()
        self.product_variant = fake.product_variant()
        self.data = {'images': [
            'test_url_image',
            'test_url_image_2'
        ]}

        self.patcher = patch('catalog.extensions.signals.create_variant_images_signal.send')
        self.mock_signal = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def call_api(self, **kwargs):
        with logged_in_user(self.iam_user):
            return super().call_api(**kwargs)

    def test_returnListVariantImages_whenCreateSuccessfully(self):
        code, body = self.call_api(data=self.data, url=self.url().format(self.product_variant.id))

        self.assertEqual(code, 200)
        self.assertIsNotNone(body.get('result').get('requestId'))
        self.mock_signal.assert_called_once()

    def test_passImagesParamIsAEmptyDict_returnDeleteSuccessfully(self):
        self.data = {'images': []}
        code, body = self.call_api(data=self.data, url=self.url().format(self.product_variant.id))

        self.assertEqual(code, 200)
        self.assertIsNotNone(body.get('result').get('requestId'))
        self.mock_signal.assert_called_once()

    def test_passImagesParam_returnUpdateSuccessfully(self):
        for _ in range(5):
            fake.variant_product_image(self.product_variant.id)

        code, body = self.call_api(data=self.data, url=self.url().format(self.product_variant.id))

        self.assertEqual(code, 200)
        self.assertIsNotNone(body.get('result').get('requestId'))
        self.mock_signal.assert_called_once()

    def test_passImagesParamIsAEmptyList_returnBadRequest(self):
        self.data = {}
        code, body = self.call_api(data=self.data, url=self.url().format(self.product_variant.id))
        self.assertEqual(code, 400)
        self.mock_signal.assert_not_called()

    def test_invalidPayloadImages_returnBadRequest(self):
        self.data = {'images': ['test_images' for _ in range(37)]}

        code, body = self.call_api(data=self.data, url=self.url().format(self.product_variant.id))
        self.assertEqual(code, 400)
        self.assertEqual(body.get('message'), 'Vượt quá giới hạn ảnh cho một biến thế (36 ảnh)')
        self.mock_signal.assert_not_called()

    def test_passNotExistVariantId_returnBadRequest(self):
        code, body = self.call_api(data=self.data, url=self.url().format(123))
        self.assertEqual(code, 400)

        self.assertEqual(body.get('message'), 'Biến thể không chính xác')
        self.mock_signal.assert_not_called()
