# coding=utf-8
from catalog import models, utils
import logging
from mock import patch
from flask_login import current_user

from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Kien.HT'
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


class AttributeSetContentTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-366'
    FOLDER = '/AttributeSet/Update'

    def setUp(self):
        super().setUp()
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [
            fake.attribute_group(set_id=self.attribute_set.id, system_group=False)
            for _ in range(2)
        ]
        group_ids = [group.id for group in self.attribute_groups]
        self.attributes = [
            fake.attribute(group_ids=group_ids)
        ]

        self.system_group = fake.attribute_group(system_group=True)

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}'

    def method(self):
        return 'PATCH'

    def test_patchAttributeSetWithName__Success(self):
        request_body = {
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

        code, body = self.call_api(data=request_body)

        self.assertEqual(200, code)

    def test_patchAttributeSetEmptyName__ReturnCode400(self):
        request_body = {
            "attributeGroups": [
                {
                    "tempId": 1,
                    "name": "",
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

        code, body = self.call_api(data=request_body)

        self.assertEqual(400, code)

    def test_updateAttributeSet__shouldKeepSystemAttributeConfigs(self):
        pass


class UpdateAttributeSetVariantTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-571'
    FOLDER = '/AttributeSet/Update/Variant'

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

    def __init_body(self, group_name, attribute_id):
        return {
            "attributeGroups": [
                {
                    "tempId": 1,
                    "name": group_name or fake.text(),
                    "parentId": 0,
                    "priority": 1,
                    "isFlat": True,
                    "level": 1,
                    "systemGroup": False,
                    "attributes": [
                        {
                            "id": attribute_id or 1,
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

    def __make_variation(self, attribute_id=0):
        attr_group_attrs = self.__get_group_attributes()
        for aga in attr_group_attrs:
            if not attribute_id or aga.attribute_id == attribute_id:
                aga.is_variation = 1
        models.db.session.commit()

    def __make_system_group(self, is_variation=0):
        for group in self.attribute_groups:
            group.system_group = True
            group.code = utils.convert(utils.slugify(group.name))
        if is_variation:
            self.__make_variation()
        models.db.session.commit()

    def __generate_name_without_dupplication(self):
        import random
        import string

        digits = "".join([random.choice(string.digits) for _ in range(6)])
        chars = "".join([random.choice(string.ascii_letters) for _ in range(18)])
        name = fake.text(length=10) + fake.text(length=10) + fake.text(length=10) + digits + chars
        return name

    def __get_group(self, group_code):
        attribute_set_id = self.attribute_set.id
        return models.AttributeGroup.query.filter(models.AttributeGroup.attribute_set_id == attribute_set_id,
                                                  models.AttributeGroup.code == group_code).first()

    def __get_group_attribute(self, group_id, attribute_id):
        return models.AttributeGroupAttribute.query.filter(
            models.AttributeGroupAttribute.attribute_group_id == group_id,
            models.AttributeGroupAttribute.attribute_id == attribute_id).first()

    def __get_group_attributes(self):
        return models.AttributeGroupAttribute.query.filter(
            models.AttributeGroupAttribute.attribute_group_id.in_(self.group_ids)).all()

    def __init_request(self):
        new_attribute = fake.attribute()
        group_name = self.__generate_name_without_dupplication()
        request_body = self.__init_body(group_name, new_attribute.id)
        code, _ = self.call_api(data=request_body)
        return code

    def test_update_attribute_set_return200_with_keep_dimension_is_not_variant(self):
        self.__create_attribute_set()
        code = self.__init_request()
        sys_group = self.__get_group('nhom-he-thong')
        self.assertEqual(200, code)
        for da in self.dimensional_attributes:
            sys_group_attribute = self.__get_group_attribute(sys_group.id, da.id)
            self.assertEqual(0, sys_group_attribute.is_variation)

    def test_update_attribute_set_return200_with_keep_other_attribute_old_not_variant_is_not_variant(self):
        code = self.__init_request()
        groups = self.__get_group_attributes()
        self.assertEqual(200, code)
        for ga in groups:
            self.assertEqual(0, ga.is_variation)

    def test_update_attribute_set_return200_with_keep_ratio_is_variant(self):
        self.__create_attribute_set()
        code = self.__init_request()
        ratio_group = self.__get_group('uom')
        ratio_group_attribute = self.__get_group_attribute(ratio_group.id, self.attribute_ratio.id)
        self.assertEqual(200, code)
        self.assertEqual(1, ratio_group_attribute.is_variation)

    def test_update_attribute_set_return200_with_keep_uom_is_variant(self):
        self.__create_attribute_set()
        code = self.__init_request()
        uom_group = self.__get_group('uom')
        uom_group_attribute = self.__get_group_attribute(uom_group.id, self.attribute_uom.id)
        self.assertEqual(200, code)
        self.assertEqual(1, uom_group_attribute.is_variation)

    def test_update_attribute_set_return200_with_keep_other_attribute_old_variant_is_variant_in_not_system_group(self):
        attribute_id = self.attributes[0].id
        new_attribute = fake.attribute(group_ids=self.group_ids[1:])
        self.__make_variation(attribute_id)
        group_name = self.__generate_name_without_dupplication()
        request_body = self.__init_body(group_name, attribute_id)
        request_body['attributeGroups'].append({
            "tempId": 2,
            "name": self.__generate_name_without_dupplication(),
            "parentId": 0,
            "priority": 1,
            "isFlat": True,
            "level": 1,
            "systemGroup": False,
            "attributes": [
                {
                    "id": new_attribute.id,
                    "priority": 1,
                    "textBefore": "",
                    "textAfter": "JZ0",
                    "isDisplayed": True,
                    "highlight": True
                }
            ]
        })
        code, _ = self.call_api(data=request_body)
        attr_group_attrs = list(
            filter(lambda x: x.attribute_id == attribute_id, self.__get_group_attributes()))
        self.assertEqual(200, code)
        for aga in attr_group_attrs:
            self.assertEqual(1, aga.is_variation)
