#coding=utf-8

import os
import io
import shutil
import base64 as b64
from mock import patch

import pytest

import config
from tests.catalog.api import APITestCase
from catalog.services import brand


class TestServiceSaveLogoBrand(APITestCase):
    ISSUE_KEY = 'SC-261'

    def tearDown(self):
        shutil.rmtree(
            os.path.join(
                config.ROOT_DIR,
                'media',
                'brand'
            ),
            ignore_errors=True
        )

    def check_content_file_saved(self, relative_path, image):
        path = os.path.join(config.ROOT_DIR, relative_path)
        with open(path, 'rb') as fp:
            file_saved = fp.read()
        assert hash(file_saved) == hash(image)

    def check_path_file_saved(self, path):
        filename = os.path.basename(path)
        assert os.path.basename(os.path.dirname(path)) == filename[0]

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_image_400x400_with_path(self, mock):
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        code = 'dell'
        mock.return_value = f'{code[0]}/{code}.png'
        ret_path = brand.save_logo_image(b64_image)
        self.assertEqual(f'{code[0]}/{code}.png', ret_path)

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_image_400x400_with_path_is_none(self, mock):
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        code = 'dell'
        path = f'{code[0]}/{code}.png'
        mock.return_value = path
        ret_path = brand.save_logo_image(b64_image)
        self.assertEqual(path, ret_path)

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_image_1201x400(self, mock):
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-1201x400.png', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        code = 'dell'
        mock.return_value = f'{code[0]}/{code}.png'
        with pytest.raises(Exception):
            brand.save_logo_image(b64_image)

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_image_400x501(self, mock):
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x1201.png', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        path = 'd/dell'
        mock.return_value = path
        with pytest.raises(Exception):
            brand.save_logo_image(b64_image)

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_image_jpg(self, mock):
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.jpg', 'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        path = 'd/dell'
        mock.return_value = path
        with pytest.raises(Exception):
            brand.save_logo_image(b64_image)

    @patch('catalog.services.brand.send_to_image_service')
    def test_save_json(self, mock):
        fp = io.BytesIO(initial_bytes=b'12346579')
        image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode('utf-8')
        path = 'd/dell'
        mock.return_value = path
        with pytest.raises(Exception):
            brand.save_logo_image(b64_image)
