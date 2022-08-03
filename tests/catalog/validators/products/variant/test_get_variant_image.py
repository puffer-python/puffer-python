import unittest

import requests
from mock import patch

from catalog.extensions.exceptions import BadRequestException
from catalog.validators.variant import UpdateVariantValidator


class MockResponseObject:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code


class ValidateGetVariantImageTestCase(unittest.TestCase):
    ISSUE_KEY = 'SC-509'

    def setUp(self):
        self.url = 'https://storage.googleapis.com/teko-gae.appspot.com/media/image/2020/3/30/20200330_2a9112dd-93ae-4424-be5d-dab896f5c2bd'

    def test_getImageSuccessfully(self):
        response = UpdateVariantValidator._validate_get_image(self.url)
        self.assertEqual(response.status_code, 200)

    @patch('catalog.validators.variant.requests.get')
    def test_fileServiceStatusCodeNotEqual200_raiseBadRequestException(self, mock_response):
        response = MockResponseObject(None, 400)
        mock_response.return_value = response

        with self.assertRaises(BadRequestException):
            UpdateVariantValidator._validate_get_image(self.url)

    @patch('catalog.validators.variant.requests.get')
    def test_fileServiceGotRequestException_returnBadRequest(self, mock_response):
        mock_response.side_effect = requests.exceptions.RequestException

        with self.assertRaises(BadRequestException):
            UpdateVariantValidator._validate_get_image(self.url)
