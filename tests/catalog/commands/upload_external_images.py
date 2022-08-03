from unittest.mock import patch

from catalog import models, app
from commands.upload_external_images import upload_external_images
from tests.catalog.api import APITestCase
from tests.faker import fake


class UploadExternalImages(APITestCase):
    def setUp(self):
        self.request_ids = [fake.failed_variant_image_request() for _ in range(10)]
        self.patcher = patch('catalog.extensions.signals.create_variant_images_signal.send')
        self.mock_signal = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_uploadFailedImages(self):
        app.test_cli_runner().invoke(cli=upload_external_images, args=['dungbc@gmail.com', '10'])

        failed_variant_image_request = models.FailedVariantImageRequest.query.filter(
            models.FailedVariantImageRequest.status.is_(True)
        ).all()

        self.assertEqual(10, len(failed_variant_image_request))




