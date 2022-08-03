#coding=utf-8

import pytest

from tests.catalog.api import APITestCase
from catalog.extensions import exceptions as exc
from tests.faker import fake

from catalog.services import brand


class TestServiceGetConcreteBrand(APITestCase):
    ISSUE_KEY = 'SC-272'

    def setUp(self):
        self.brand = fake.brand()

    def test_get_brand_existed(self):
        ret = brand.get_brand(self.brand.id)
        self.assertEqual(ret, self.brand)

    def test_get_brand_not_exist(self):
        with pytest.raises(exc.BadRequestException):
            brand.get_brand(fake.integer() + 1)

