# coding=utf-8
import logging

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import models as m

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class AttributeSetVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-584'
    FOLDER = '/AttributeSet/Create/VariantAttribute'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}/variation_attributes'

    def method(self):
        return 'POST'

    def __init_attributes_groups(self, n):
        self.attribute_groups = [
            fake.attribute_group(set_id=self.attribute_set.id, system_group=False)
        ]
        group_ids = [group.id for group in self.attribute_groups for _ in range(n*n)]
        self.attributes = [
            fake.attribute(group_ids=group_ids, is_variation=True, value_type='selection')
            for _ in range(n)
        ]
        self.no_variant_attribute = fake.attribute(group_ids=group_ids, value_type='selection')
        m.db.session.commit()

    def __init_variant_attribute_for_attribute_set(self):
        return {'attributeId': self.no_variant_attribute.id, 'variationDisplayType': 'text'}

    def __get_attribute_group(self):
        return m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.attribute_id == self.no_variant_attribute.id
        ).join(m.AttributeGroup).filter(
            m.AttributeGroup.attribute_set_id == self.attribute_set.id
        ).first()

    def __init_request(self, number_variant_attributes):
        self.__init_attributes_groups(number_variant_attributes)
        data = self.__init_variant_attribute_for_attribute_set()
        return self.call_api_with_login(data=data)

    def test_create_variant_attribute_return200_with_3_variants_of_set(self):
        code, _ = self.__init_request(2)

        self.assertEqual(200, code)
        attribute_group = self.__get_attribute_group()
        self.assertEqual(1, attribute_group.is_variation)

    def test_create_variant_attribute_return200_with_4_variants_of_set(self):
        code, _ = self.__init_request(3)

        self.assertEqual(200, code)
        attribute_group = self.__get_attribute_group()
        self.assertEqual(1, attribute_group.is_variation)

    def test_create_variant_attribute_return400_with_5_variants_of_set(self):
        code, response = self.__init_request(4)

        self.assertEqual(400, code)
        self.assertEqual('Một bộ thuộc tính chỉ có tối đa 4 thuộc tính biến thể', response['message'])
        attribute_group = self.__get_attribute_group()
        self.assertEqual(0, attribute_group.is_variation)

    def test_create_variant_attribute_return400_with_10_variants_of_set(self):
        code, response = self.__init_request(9)

        self.assertEqual(400, code)
        self.assertEqual('Một bộ thuộc tính chỉ có tối đa 4 thuộc tính biến thể', response['message'])
        attribute_group = self.__get_attribute_group()
        self.assertEqual(0, attribute_group.is_variation)
