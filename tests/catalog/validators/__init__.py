# coding=utf-8
import logging
import unittest

import pytest

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('session')
class BaseValidatorTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._validator = None
        self._schema = None

    def declare_schema(self, schema_cls):
        self._schema = schema_cls

    def invoke_validator(self, validator_cls):
        self._validator = validator_cls

    def do_validate(self, data, obj_id=None, **kwargs):
        data = self._schema(**kwargs).load(data)
        self._validator.validate(data, obj_id)
