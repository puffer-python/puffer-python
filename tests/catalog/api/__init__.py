# coding=utf-8
# pylint: disable=no-member
# pylint: disable=assignment-from-none  
import logging
import unittest
import pytest
import json
import os

import config
from tests import logged_in_user
from catalog import app
from tests.utils import JiraTest

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class APIBaseTestCase(JiraTest):
    FOLDER = '/'

    def url(self):
        raise NotImplementedError("Cần khai báo url API")

    def headers(self):
        return None

    def method(self):
        raise NotImplementedError("Cần khai báo method của API")

    def send_request(self, data=None, content_type=None, method=None, url=None):
        """
        Send request theo method và url

        :param data:
        :param content_type:
        :param method:
        :param url:
        :return:
        """
        meth = method or self.method()
        headers = self.headers()
        if meth.lower() != 'get':
            content_type = content_type or 'application/json'

        if content_type == 'application/json' and data:
            data = json.dumps(data)
        method = getattr(self.client, meth.lower())
        url = url or self.url()
        if data == {}:
            res = method(url, json=data, content_type=content_type, headers=headers)
        else:
            res = method(url, data=data, content_type=content_type, headers=headers)
        return res

    def call_api(self, data=None, content_type=None, method=None, url=None):
        """
        Alias for send_request. It will just return status_code & json data

        :rtype: (int, dict): (status_code, response body)
        """
        res = self.send_request(data, content_type, method=method, url=url)

        code = res.status_code
        if res.headers.get('Content-Type') == 'application/json':
            body = res.json
            if body:
                self.assert_response_body(body)
        else:
            body = res.get_data()

        return code, body

    def call_api_with_login(self, data=None, content_type=None, method=None, url=None):
        """
        Alias for send_request. It will just return status_code & json data

        :rtype: (int, dict): (status_code, response body)
        """
        with logged_in_user(self.user):
            return self.call_api(data, content_type, method, url)

    @staticmethod
    def assert_response_body(body):
        """

        :param body:
        :return:
        """
        from marshmallow import fields, Schema, validates_schema, ValidationError

        class ResponseSchema(Schema):
            code = fields.String()
            message = fields.String()
            result = fields.Raw(allow_none=True)

            @validates_schema
            def validate_result_field(self, data, **kwargs):
                result = data.get('result')
                if result and not type(result) in (dict, list):
                    raise ValidationError("Result must be of type dict or list")

            @classmethod
            def assert_response_body(cls, data):
                validator = cls()
                assert not validator.validate(data), 'Invalid response format'

        ResponseSchema.assert_response_body(body)

    def assert_import_template_file(self, file_name, body):
        file_path = os.path.join(
            config.ROOT_DIR,
            'storage',
            'template',
            file_name
        )
        with open(file_path, 'rb') as f:
            file_content = f.read()
        self.assertEqual(len(body), len(file_content))
        for j in range(0, len(body)):
            self.assertEqual(body[j], file_content[j])


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session')
@pytest.mark.usefixtures('all_tests')
class APITestCase(unittest.TestCase, APIBaseTestCase):
    pass


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('session_class')
class APITestCaseClassScoped(unittest.TestCase, APIBaseTestCase):
    pass


@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('mysql_session')
class APITestCaseWithMysql(unittest.TestCase, APIBaseTestCase):

    @classmethod
    def tearDownClass(cls):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

@pytest.mark.usefixtures('client_class')
@pytest.mark.usefixtures('mysql_session_by_func')
class APITestCaseWithMysqlByFunc(unittest.TestCase, APIBaseTestCase):

    @classmethod
    def tearDownClass(cls):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
