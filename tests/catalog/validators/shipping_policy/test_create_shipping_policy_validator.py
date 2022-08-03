# coding=utf-8
import logging
import random
import pytest

from catalog import models as m
from catalog.extensions import exceptions as exc, marshmallow as mm
from catalog.api.shipping_policy.schema import ShippingPolicyCreateRequest
from catalog.validators.shipping_policy import CreateShippingPolicyValidator
from tests.catalog.validators import BaseValidatorTestCase
from tests.faker import fake
from tests.utils import JiraTest

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateShippingPolicyValidatorTestCase(BaseValidatorTestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-56'

    def setUp(self):
        super().setUp()
        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]

        for code in ['all', 'bulky', 'near']:
            fake.misc(data_type='shipping_type', code=code)

        self.data = {
            'name': fake.text(length=200),
            'isActive': True,
            'shippingType': random.choice(['all', 'bulky', 'near']),
            'providerIds': [provider.id for provider in self.providers],
            'categoryIds': [category.id for category in self.categories]
        }

        self.declare_schema(ShippingPolicyCreateRequest)
        self.invoke_validator(CreateShippingPolicyValidator)

    def test_passNameExisted__raiseBadRequestException(self):
        policy = fake.shipping_policy()
        self.data['name'] = policy.name
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_passNameLongerThan255__raiseValidationError(self):
        self.data['name'] = fake.text(length=256)
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data)

    def test_isActiveNotBoolean__raiseValidationError(self):
        self.data['isActive'] = 6969
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data)

    def test_shippingTypeNotValid__raiseValidationError(self):
        self.data['shippingType'] = 'blabla'
        with pytest.raises(mm.ValidationError):
            self.do_validate(self.data)

    def test_providerNotExists__raiseBadRequestException(self):
        self.data['providerIds'] = [696969]
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_providerInactive__raiseBadRequestException(self):
        provider = fake.seller_prov()
        provider.is_active = False
        m.db.session.commit()
        self.data['providerIds'] = [provider.id]
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def testCategoryNotExists__raiseBadRequestException(self):
        self.data['categoryIds'] = [849234]
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)

    def test_samePolicyExisted__raiseBadRequestException(self):
        policy = fake.shipping_policy(
            provider_ids=[self.providers[0].id],
            category_ids=[self.categories[0].id]
        )
        with pytest.raises(exc.BadRequestException):
            self.do_validate(self.data)
