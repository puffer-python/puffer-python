# coding=utf-8
import logging
import random
import base64 as b64
import shutil

import os
import pytest

import config
from tests.faker import fake
from catalog.extensions import marshmallow as mm
from catalog.api.brand import schema
from catalog.extensions import exceptions as exc
from catalog.validators.brand import CreateBrandValidator as Validator
from tests.catalog.validators import BaseValidatorTestCase

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateBrandValidatorTestCase(BaseValidatorTestCase):
    ISSUE_KEY = 'SC-306'

    def setUp(self):
        super().setUp()
        self.data = {
            'name': fake.name(),
            'code': fake.text(),
            'docRequest': random.choice([True, False])
        }
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png',
                  'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode(
            'utf-8')
        self.data['logo'] = b64_image
        self.declare_schema(schema.BrandRequest)
        self.invoke_validator(Validator)

    def test_passValidData__runSuccess(self):
        self.do_validate(self.data)

    def test_NameExisted__raiseBadRequestException(self):
        brand = fake.brand()
        self.data['name'] = brand.name
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_missingName__raiseValidationException(self):
        self.data.pop('name')
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data)

    def test_codeInvalid__raiseBadRequestException(self):
        self.data['code'] = '<>":{P}+'
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_codeExisted__raiseBadRequestException(self):
        brand = fake.brand()
        self.data['code'] = brand.code
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_codeExistedCaseSensitive__raiseBadRequestException(self):
        brand = fake.brand()
        self.data['code'] = ''.join(
            [random.choice([c, c.upper()]) for c in brand.code]
        )
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_codeLenGreaterThan100__raiseBadRequestException(self):
        self.data['code'] = 'a'*1000
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_docRequestNotBooleanValue__raiseValidationException(self):
        self.data['docRequest'] = 'abc'
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data)

    def test_logoTypeJPG__raiseBadRequestException(self):
        pass

    def test_corruptImageData__raiseBadRequestException(self):
        pass

    def tearDown(self):
        shutil.rmtree(
            os.path.join(
                config.ROOT_DIR,
                'media',
                'brand'
            ),
            ignore_errors=True
        )
