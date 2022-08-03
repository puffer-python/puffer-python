# coding=utf-8
import logging
import random
import pytest

from catalog import models as m
from catalog.extensions import exceptions as exc, marshmallow as mm
from catalog.api.shipping_policy.schema import ShippingPolicyUpdateRequest
from catalog.validators.shipping_policy import UpdateShippingPolicyValidator
from tests.catalog.validators import BaseValidatorTestCase
from tests.faker import fake
from tests.utils import JiraTest

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UpdateShippingPolicyValidatorTestCase(BaseValidatorTestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-59'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]

        for code in ['all', 'bulky', 'near']:
            fake.misc(data_type='shipping_type', code=code)

        self.policy = fake.shipping_policy(
            category_ids=[category.id for category in self.categories],
            provider_ids=[provider.id for provider in self.providers]
        )

        self.declare_schema(ShippingPolicyUpdateRequest)
        self.invoke_validator(UpdateShippingPolicyValidator)

    def test_passNameExisted__raiseBadRequestException(self):
        policy = fake.shipping_policy()
        data = {
            'name': policy.name
        }
        with pytest.raises(exc.BadRequestException):
            self.do_validate(data)

    def test_passNameLongerThan255__raiseValidationError(self):
        data = {
            'name': fake.text(length=256)
        }
        with pytest.raises(mm.ValidationError):
            self.do_validate(data, self.policy.id)

    def test_isActiveNotBoolean__raiseValidationError(self):
        data = {
            'isActive': 6969
        }
        with pytest.raises(mm.ValidationError):
            self.do_validate(data, self.policy.id)

    def test_shippingTypeNotValid__raiseValidationException(self):
        data = {
            'shippingType': "abcsdfd"
        }
        with pytest.raises(mm.ValidationError):
            self.do_validate(data, self.policy.id)

    def test_providerInactive__raiseBadRequestException(self):
        provider = fake.seller_prov()
        provider.is_active = False
        m.db.session.commit()
        data = {
            'providerIds': [provider.id]
        }
        with pytest.raises(exc.BadRequestException):
            self.do_validate(data)

    def testCategoryNotExists__raiseBadRequestException(self):
        data = {
            'categoryIds': [856452]
        }
        with pytest.raises(exc.BadRequestException):
            self.do_validate(data, self.policy.id)
