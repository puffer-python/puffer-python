# coding=utf-8
import logging
import random
import base64 as b64
import pytest
import config

from tests.catalog.validators import BaseValidatorTestCase
from tests.faker import fake
from catalog.api.brand import schema
from catalog.validators.brand import UpdateBrandValidator as Validator
from catalog.extensions import exceptions as exc, marshmallow as mm

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UpdateBrandValidatorTestCase(BaseValidatorTestCase):
    def setUp(self):
        self.brand = fake.brand()
        self.fake_brand = fake.brand()
        self.inactive_brand = fake.brand(is_active=False)
        self.data = {
            'name': fake.name(),
            'docRequest': random.choice((True, False)),
            'isActive': True
        }
        with open(f'{config.ROOT_DIR}/tests/datafiles/brand-logo-400x400.png',
                  'rb') as fp:
            image = fp.read()
        b64_image = 'data:image/png;base64,' + b64.b64encode(image).decode(
            'utf-8')
        self.data['logo'] = b64_image
        self.declare_schema(schema.BrandUpdateRequest)
        self.invoke_validator(Validator)

    def test_brandNameExisted__raiseBadRequestException(self):
        self.data['name'] = self.fake_brand.name
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data, self.brand.id)

    def test_brandNameLargerThan100Character__raiseBadRequestException(self):
        self.data['name'] = 'a' * 101
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data, self.brand.id)
