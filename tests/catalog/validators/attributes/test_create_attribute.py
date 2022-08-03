# coding=utf-8

import pytest
from unittest import TestCase
from marshmallow import ValidationError
from catalog.extensions import exceptions as exc
from catalog.validators.attribute import CreateAttributeValidator
from catalog.api.attribute import schema
from tests.catalog.api import APITestCase
from tests.utils import JiraTest
from tests.faker import fake



class CreateAttributeValidateTestCase(APITestCase, JiraTest):
    ISSUE_KEY='SC-604'

    def setUp(self):
        self.attribute = fake.attribute()
        value_type = fake.attribute_value_type()
        unit = fake.attribute_unit()
        self.data = {
            'name': fake.hexify() + 'tiếng việt',
            'displayName': fake.hexify() + 'tiếng việt',
            'code': fake.text(),
            'unitId': unit.id,
            'valueType': value_type,
            'description': fake.text() + 'tiếng việt',
            'isRequired': fake.boolean(),
            'isSearchable': fake.boolean(),
            'isFilterable': True if value_type in ('selection', 'multiple_select') else False
        }

    def run_validator(self):
        data = schema.AttributeCreateData().load(self.data)
        CreateAttributeValidator.validate(data)

    def test_passValidData__passValidate(self):
        self.run_validator()

    def test_passUnitIdNotExist__raiseBadRequestException(self):
        self.data['unitId'] += 1
        with pytest.raises(exc.BadRequestException) as err_info:
            self.run_validator()
        assert err_info.value.message == 'Dữ liệu không thỏa mãn'

    def test_isFilterableIsTrueWhenValueTypeIsText__raiseBadRequestException(self):
        self.data['valueType'] = 'text'
        self.data['isFilterable'] = True
        with pytest.raises(exc.BadRequestException) as err_info:
            self.run_validator()

    def test_passCodeExisted__raiseBadRequestException(self):
        self.data['code'] = self.attribute.code
        with pytest.raises(exc.BadRequestException) as err_info:
            self.run_validator()
        assert err_info.value.message == 'Dữ liệu không thỏa mãn'

    def test_passNameExisted__raiseBadRequestException(self):
        self.data['name'] = self.attribute.name
        with pytest.raises(exc.BadRequestException) as err_info:
            self.run_validator()
        assert err_info.value.message == 'Dữ liệu không thỏa mãn'

    def test_passNameOnlySpace__raiseValidationError(self):
        self.data['name'] = ' ' * 5
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passNameSoLong__raiseValidationError(self):
        self.data['name'] = fake.text(300)
        with pytest.raises(ValidationError):
            self.run_validator()
