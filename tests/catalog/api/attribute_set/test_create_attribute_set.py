# coding=utf-8
import logging
from mock import patch
from tests.faker import fake
from catalog.biz.attribute_set import add_system_groups
from catalog import models as m

from tests.catalog.api import APITestCase

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class CreateAttributeSetTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-366'
    FOLDER = '/AttributeSet/Create'

    def setUp(self):
        super().setUp()
        self.data = {
            "attributeGroups": [
                {
                    "tempId": 1,
                    "name": "a",
                    "parentId": 0,
                    "priority": 1,
                    "isFlat": True,
                    "level": 1,
                    "systemGroup": False,
                    "attributes": [
                        {
                            "id": 1,
                            "priority": 1,
                            "textBefore": "",
                            "textAfter": "JZ0",
                            "isDisplayed": True,
                            "highlight": True
                        }
                    ]
                }
            ]
        }

    def test_createNewAttributeSet__shouldAddUoMAttributeConfig(self):
        pass

    def test_createNewAttributeSet__shouldAddPackedAttributeConfig(self):
        pass


class CreateAttributeSetWithVariantTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-571'
    FOLDER = '/AttributeSet/Create/Variant'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_uom = fake.attribute(code='uom')
        self.attribute_ratio = fake.attribute(code='uom_ratio')
        self.data = {"name": fake.text()}
        self.patcher = patch('catalog.extensions.signals.attribute_set_created_signal.send')
        self.mock_signal = self.patcher.start()

    def url(self):
        return f'/attribute_sets'

    def method(self):
        return 'POST'

    def __get_group(self, attribute_set_id, group_code):
        return m.AttributeGroup.query.filter(m.AttributeGroup.attribute_set_id == attribute_set_id,
                                             m.AttributeGroup.code == group_code).first()

    def __get_group_attribute(self, group_id, attribute_id):
        return m.AttributeGroupAttribute.query.filter(m.AttributeGroupAttribute.attribute_group_id == group_id,
                                                      m.AttributeGroupAttribute.attribute_id == attribute_id).first()

    def test_create_attribute_set_return200_with_uom_is_variant(self):
        code, response = self.call_api_with_login(data=self.data)
        attribute_set_id = response['result']['id']
        add_system_groups(attribute_set_id)
        uom_group = self.__get_group(attribute_set_id, 'uom')
        uom_group_attribute = self.__get_group_attribute(uom_group.id, self.attribute_uom.id)

        self.assertEqual(200, code)
        self.mock_signal.assert_called_once()
        self.assertEqual(1, uom_group_attribute.is_variation)

    def test_create_attribute_set_return200_with_ratio_is_variant(self):
        code, response = self.call_api_with_login(data=self.data)
        attribute_set_id = response['result']['id']
        add_system_groups(attribute_set_id)
        ratio_group = self.__get_group(attribute_set_id, 'uom')
        ratio_group_attribute = self.__get_group_attribute(ratio_group.id, self.attribute_ratio.id)

        self.assertEqual(200, code)
        self.mock_signal.assert_called_once()
        self.assertEqual(1, ratio_group_attribute.is_variation)

    def test_create_attribute_set_return200_with_dimensional_is_not_variant(self):
        DIMENSIONAL_ATTRIBUTE_CODES = [
            'weight',
            'width',
            'length',
            'height',
            'pack_weight',
            'pack_width',
            'pack_length',
            'pack_height'
        ]
        dimensional_attributes = []
        for attribute_code in DIMENSIONAL_ATTRIBUTE_CODES:
            attribute = fake.attribute(code=attribute_code)
            dimensional_attributes.append(attribute)
        code, response = self.call_api_with_login(data=self.data)
        attribute_set_id = response['result']['id']
        add_system_groups(attribute_set_id)
        sys_group = self.__get_group(attribute_set_id, 'nhom-he-thong')

        self.assertEqual(200, code)
        self.mock_signal.assert_called_once()
        priority = -1
        for da in dimensional_attributes:
            sys_group_attribute = self.__get_group_attribute(sys_group.id, da.id)
            self.assertEqual(0, sys_group_attribute.is_variation)
            self.assertLess(priority, sys_group_attribute.priority)
            priority = sys_group_attribute.priority

