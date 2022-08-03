# coding=utf-8
from catalog.validators.attribute_set import Group
import logging
from flask_login import current_user

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import models, utils
from mock import patch

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)

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


class AttributeSetUpdateAllowFlatTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-603'
    FOLDER = '/AttributeSet/Update/SystemGroup'

    def setUp(self):
        super().setUp()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [
            fake.attribute_group(set_id=self.attribute_set.id, system_group=False)
            for _ in range(2)
        ]
        self.group_ids = [group.id for group in self.attribute_groups]
        self.attributes = [
            fake.attribute(group_ids=self.group_ids)
        ]
        self.dimensional_attributes = []

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}'

    def method(self):
        return 'PATCH'

    def __create_attribute_set(self):
        from catalog.biz.attribute_set import add_system_groups
        patcher = patch('catalog.extensions.signals.attribute_set_created_signal.send')
        mock_signal = patcher.start()
        mock_signal.return_value = True
        self.attribute_uom = fake.attribute(code='uom')
        self.attribute_ratio = fake.attribute(code='uom_ratio')
        for attribute_code in DIMENSIONAL_ATTRIBUTE_CODES:
            self.dimensional_attributes.append(fake.attribute(code=attribute_code))
        _, response = self.call_api_with_login(data={'name': fake.text()}, url="/attribute_sets", method='POST')
        set_id = response['result']['id']
        add_system_groups(set_id)
        self.attribute_set = models.AttributeSet.query.filter(
            models.AttributeSet.id == set_id).first()

    def __init_body(self, group, attribute_ids):
        attributes = []
        idx = 1
        for attribute_id in attribute_ids:
            attributes.append({
                "id": attribute_id,
                "priority": idx,
                "textBefore": f"TEXTBEFORE{attribute_id}",
                "textAfter": f"TEXTAFTER{attribute_id}",
                "isDisplayed": True,
                "highlight": True
            })
            idx += 1
        return {
            "attributeGroups": [
                {
                    "tempId": group.id,
                    "name": group.name,
                    "parentId": 0,
                    "priority": 1,
                    "isFlat": True,
                    "level": 1,
                    "systemGroup": True,
                    "attributes": attributes
                }
            ]
        }

    def __get_group(self, group_code):
        attribute_set_id = self.attribute_set.id
        return models.AttributeGroup.query.filter(models.AttributeGroup.attribute_set_id == attribute_set_id,
                                                  models.AttributeGroup.code == group_code).first()

    def __get_group_attribute(self, group_id, attribute_id):
        return models.AttributeGroupAttribute.query.filter(models.AttributeGroupAttribute.attribute_group_id == group_id,
                                                           models.AttributeGroupAttribute.attribute_id == attribute_id).first()

    def __equal_group_attribute(self, attribute, priority):
        self.assertEqual(priority, attribute.priority)
        self.assertEqual(f"TEXTBEFORE{attribute.attribute_id}", attribute.text_before)
        self.assertEqual(f"TEXTAFTER{attribute.attribute_id}", attribute.text_after)
        self.assertEqual(True, attribute.is_displayed)
        self.assertEqual(True, attribute.highlight)

    def test_update_attribute_set_return200_with_not_change_attributes(self):
        self.__create_attribute_set()
        group = self.__get_group('nhom-he-thong')
        request_body = self.__init_body(group, list(map(lambda x: x.id, self.dimensional_attributes)))
        code, _ = self.call_api(data=request_body)
        group = self.__get_group('nhom-he-thong')
        self.assertEqual(200, code)
        self.assertEqual(1, group.is_flat)
        idx = 1
        for dim_attr in self.dimensional_attributes:
            attribute_group = self.__get_group_attribute(group.id, dim_attr.id)
            self.__equal_group_attribute(attribute_group, idx)
            idx += 1

    def test_update_attribute_set_return400_with_add_more_attributes(self):
        self.__create_attribute_set()
        group = self.__get_group('nhom-he-thong')
        attrs = list(map(lambda x: x.id, self.dimensional_attributes))
        attrs.append(self.attributes[0].id)
        request_body = self.__init_body(group, attrs)
        code, res = self.call_api(data=request_body)
        self.assertEqual(400, code)
        self.assertEqual(f'Group {group.name} bị thay đổi thuộc tính', res['message'])

    def test_update_attribute_set_return400_with_remove_attributes(self):
        self.__create_attribute_set()
        group = self.__get_group('nhom-he-thong')
        attrs = list(map(lambda x: x.id, self.dimensional_attributes))
        attrs.remove(self.dimensional_attributes[0].id)
        request_body = self.__init_body(group, attrs)
        code, res = self.call_api(data=request_body)
        self.assertEqual(400, code)
        self.assertEqual(f'Group {group.name} bị thay đổi thuộc tính', res['message'])
