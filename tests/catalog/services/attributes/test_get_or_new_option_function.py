# coding=utf-8
from abc import ABC

from tests.faker import fake
from tests.catalog.api import APITestCase
from tests import logged_in_user
from catalog.services.attributes import get_or_new_option


class TestGetOrNewOptionFunction(APITestCase, ABC):

    def setUp(self):
        self.user = fake.iam_user()

    def testOptionUOM(self):
        with logged_in_user(self.user):
            attribute = fake.attribute(code='uom')
            option_value = fake.text()
            result = get_or_new_option(option_value, attribute)
            self.assertIsNone(result)

    def testOptionNotUOM(self):
        with logged_in_user(self.user):
            attribute = fake.attribute(code='uom')
            if attribute.code == 'uom':
                attribute.code = fake.code = fake.text()

            option_value = fake.text()
            result = get_or_new_option(option_value, attribute)
            self.assertIsNotNone(result)
            self.assertEqual(option_value, getattr(result, 'value'))

    def testLowerTextOption(self):
        with logged_in_user(self.user):
            attribute = fake.attribute(value_type='selection')
            option = fake.attribute_option(attribute.id, seller_id=self.user.seller_id)
            result = get_or_new_option(option.value.upper(), attribute)
            self.assertIsNotNone(result)
            self.assertEqual(option.value, getattr(result, 'value'))

    def testCapitalizeOption(self):
        with logged_in_user(self.user):
            attribute = fake.attribute(value_type='selection')
            option = fake.attribute_option(attribute.id, seller_id=self.user.seller_id)
            result = get_or_new_option(option.value.capitalize(), attribute)
            self.assertIsNotNone(result)
            self.assertEqual(option.value, getattr(result, 'value'))
