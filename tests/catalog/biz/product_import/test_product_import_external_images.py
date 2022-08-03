from unittest.mock import patch

from catalog import models
from catalog.biz.product_import.images import import_variant_images
from catalog.models import db
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class MockResponse:
    def __init__(self, status_code, headers, content=None, image_url=None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.image_url = image_url

    def json(self):
        return {
            'image_url': self.image_url
        }


class MockAppRequestContext:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        pass


@patch('catalog.biz.product_import.images.requests.get')
@patch('catalog.biz.product_import.images.requests.post')
class TestImportVariantImages(APITestCase):
    ISSUE_KEY = 'CATALOGUE-342'

    def setUp(self):
        self.iam_user = fake.iam_user()
        self.product_variant = fake.product_variant()
        self.product_variant_id = self.product_variant.id
        self.output_url = 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
        self.urls = 'test.urls'

        self.file_service_response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '1048576'
            },
            image_url=self.output_url
        )
        db.session.commit()

        self.request_ctx_stack_push_patcher = patch('catalog.biz.product_import.images._request_ctx_stack.push')
        self.mock_request_ctx_stack_push = self.request_ctx_stack_push_patcher.start()
        self.app_request_context_patcher = patch('catalog.biz.product_import.create_product.app.request_context')
        self.mock_app_request_context = self.app_request_context_patcher.start()
        self.mock_app_request_context.return_value = MockAppRequestContext(self.iam_user)

    def tearDown(self):
        self.request_ctx_stack_push_patcher.stop()
        self.app_request_context_patcher.stop()

    def test__passVariantIdAndRawURLs__createSuccessfully(self, mock_post, mock_get):
        email = self.iam_user.email

        raw_input_response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '1048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )

        mock_get.return_value = raw_input_response
        mock_post.return_value = self.file_service_response

        with logged_in_user(self.iam_user):
            # Create cases
            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='1',
                email=email
            )
            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).order_by(
                models.VariantImage.priority.asc()
            ).all()

            self.assertEqual(len(images), 1)
            self.assertEqual(self.output_url, images[0].url)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 1)

            # Update cases
            self.urls = 'test.urls\ntest.urls'

            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='2',
                email=email,
                max_creatable_image=36
            )
            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).all()

            self.assertEqual(len(images), 2)
            for image in images:
                self.assertIsNotNone(image.created_by)
                self.assertIsNotNone(image.updated_by)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 3)

            # Delete cases
            self.urls = []

            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='3',
                email=email
            )

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).all()

            self.assertEqual(len(images), 0)
            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 4)

    def test__passInvalidContentLengthRawURLs(self, mock_post, mock_get):
        response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '3048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )
        self.file_service_response.image_url = []

        mock_get.return_value = response
        mock_post.return_value = self.file_service_response

        with logged_in_user(self.iam_user):
            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='1',
                email=self.iam_user.email
            )

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).all()

            self.assertEqual(len(images), 0)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].result, 'Ảnh không được vượt quá 2MB')

    def test__passInvalidContentTypeRawURLs(self, mock_post, mock_get):
        response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/xlsx',
                'Content-Length': '1048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )
        self.file_service_response.image_url = []

        mock_get.return_value = response
        mock_post.return_value = self.file_service_response

        with logged_in_user(self.iam_user):
            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='1',
                email=self.iam_user.email
            )

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).all()

            self.assertEqual(len(images), 0)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].result, 'Ảnh không đúng định dạng')

    def test__responseStatus400(self, mock_post, mock_get):
        response = MockResponse(
            status_code=400,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '1048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )
        self.file_service_response.image_url = []

        mock_get.return_value = response
        mock_post.return_value = self.file_service_response

        with logged_in_user(self.iam_user):
            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='1',
                email=self.iam_user.email
            )

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).all()

            self.assertEqual(len(images), 0)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].result, 'Hệ thống đang gặp lỗi. Vui lòng thử lại sau')

    def test__passVariantIdAndRawURLsUpto5(self, mock_post, mock_get):
        raw_input_response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '1048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )
        self.urls = 'test.urls\ntest.urls\ntest.urls\ntest.urls\ntest.urls\ntest.urls\ntest.urls\ntest.urls\ntest.urls\n'

        mock_get.return_value = raw_input_response
        mock_post.return_value = self.file_service_response

        with logged_in_user(self.iam_user):
            import_variant_images(
                variant_id=self.product_variant_id,
                urls=self.urls,
                request_id='1',
                email=self.iam_user.email,
                max_creatable_image=5
            )

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_id
            ).order_by(
                models.VariantImage.priority.asc()
            ).all()

            self.assertEqual(len(images), 5)
            self.assertEqual(self.output_url, images[0].url)

            logs = models.VariantImageLog.query.all()
            self.assertEqual(len(logs), 9)

            self.assertEqual(
                len(list(filter(lambda log: log.result == "Hệ thống chỉ cho phép tối đa 5 ảnh mỗi biến thể", logs))),
                4
            )

    def test_raiseTypeErrorException__writeErrorMessageToLog(self, mock_post, mock_get):
        error = "Hệ thống gặp lỗi"

        raw_input_response = MockResponse(
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Content-Length': '1048576'
            },
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
        )

        mock_get.return_value = raw_input_response
        mock_post.side_effects = self.file_service_response

        with logged_in_user(self.iam_user):
            # Create cases
            with patch('catalog.biz.product_import.images.update_image') as mock_current_user:
                mock_current_user.side_effect = TypeError(error)

                import_variant_images(
                    variant_id=self.product_variant_id,
                    urls=self.urls,
                    request_id='1',
                    email=None
                )
                images = models.VariantImage.query.filter(
                    models.VariantImage.product_variant_id == self.product_variant_id
                ).order_by(
                    models.VariantImage.priority.asc()
                ).all()

                logs = models.VariantImageLog.query.all()

                self.assertEqual(len(images), 0)
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0].result, error)

    def test_passDuplicateRequestId__replaceOldDBRecords(self, mock_post, mock_get):
            email = self.iam_user.email

            raw_input_response = MockResponse(
                status_code=200,
                headers={
                    'Content-Type': 'image/png',
                    'Content-Length': '1048576'
                },
                content=b'\xff\xd8\xff\xe0\x00\x10JFIF'
            )

            mock_get.return_value = raw_input_response
            mock_post.return_value = self.file_service_response

            with logged_in_user(self.iam_user):
                # Create cases
                import_variant_images(
                    variant_id=self.product_variant_id,
                    urls=self.urls,
                    request_id='1',
                    email=email
                )
                logs = models.VariantImageLog.query.all()
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0].result, "Thành công")
                self.assertEqual(logs[0].success_url, self.output_url)

                logs[0].result = "Hệ thống gặp lỗi"
                models.db.session.commit()

                # Duplicate request_id
                logs_before_id = models.VariantImageLog.query.all()[0].id
                import_variant_images(
                    variant_id=self.product_variant_id,
                    urls=self.urls,
                    request_id='1',
                    email=email
                )
                images = models.VariantImage.query.filter(
                    models.VariantImage.product_variant_id == self.product_variant_id
                ).order_by(
                    models.VariantImage.priority.asc()
                ).all()

                self.assertEqual(len(images), 1)
                self.assertEqual(self.output_url, images[0].url)

                logs_after = models.VariantImageLog.query.all()
                self.assertEqual(len(logs_after), 1)
                self.assertEqual(logs_after[0].result, "Thành công")
                self.assertEqual(logs_after[0].success_url, self.output_url)

                self.assertEqual(logs_after[0].id, logs_before_id)

    def test_invalidVariantId(self, mock_post, mock_get):
        """
        Always make sure the input variant_id are valid
        """
        pass

