import pytest
from mock import patch
import requests
import random

from catalog.biz.product_import.images import download_from_internet

class TestDownloadImage:
    ISSUE_KEY = 'CATALOGUE-1035'
    FOLDER = '/Import/DownloadImage'

    drive_image_url = 'https://drive.google.com/file/d/1hFvRxukw3oOt_w91fslUKavmxiFcnS3Q/view'
    invalid_url = 'https://google.com'

    def test_download_image_return_200_with_valid_url(self):
        get_response = requests.Response()
        get_response.status_code = 200
        image_type = ['jpeg', 'png', 'jpg']
        get_response.headers['content-type'] = 'image/' + random.choice(image_type)

        with patch('requests.get') as mock_response:
            mock_response.return_value = get_response
            response = download_from_internet(self.drive_image_url, verify=True)
            assert response.status_code == 200
            assert 'image' in response.headers.get('content-type')

    def test_download_image_return_404_with_invalid_url(self):
        get_response = requests.Response()
        get_response.status_code = 404
        get_response.headers['content-type'] = 'text/html'

        with patch('requests.get') as mock_response:
            mock_response.return_value = get_response
            response = download_from_internet(self.invalid_url, verify=True)
            assert response.status_code == 404
            assert 'html' in response.headers.get('content-type')

