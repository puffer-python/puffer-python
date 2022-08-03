#coding=utf-8

import pytest

from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators import imports as validators


class GetTemplateImportProductValidatorTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-329'
    FOLDER = '/CreateProductTemplate/Validate'

    def run_validator(self):
        validators.CreateGeneralTemplateValidator.validate({
            'attribute_set_id': self.attribute_set_id,
            'template_type': 'general'
        })

    def test_passAttributeSetExist__allowPassValidator(self):
        self.attribute_set_id = fake.attribute_set().id
        self.run_validator()

    def test_passAttributeSetNotExist__raiseBadRequestException(self):
        self.attribute_set_id = fake.random_int(100)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Bộ thuộc tính không tồn tại'
