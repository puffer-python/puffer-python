# coding=utf-8
import logging
import random

import config
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.constants import UOM_CODE_ATTRIBUTE, ATTRIBUTE_TYPE
from catalog import models

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


class AttributeSetContentTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-864'
    FOLDER = '/HN1/AttributeSet/Get'

    def setUp(self):
        super().setUp()
        self.seller_id = fake.integer()
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [
            fake.attribute_group(set_id=self.attribute_set.id, system_group=False)
            for _ in range(2)
        ]
        group_ids = [group.id for group in self.attribute_groups]
        self.attributes = [
            fake.attribute(group_ids=group_ids,
                           value_type=random.choice([
                               ATTRIBUTE_TYPE.SELECTION,
                               ATTRIBUTE_TYPE.MULTIPLE_SELECT
                           ]))
        ]

    def setUOM(self, seller_id=None):
        uom_attribute = random.choice(self.attributes)
        uom_attribute.code = UOM_CODE_ATTRIBUTE
        uom_attribute.value_type = ATTRIBUTE_TYPE.SELECTION
        self.uom_option = fake.attribute_option(
            attribute_id=uom_attribute.id, seller_id=seller_id or self.seller_id)

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}'

    def method(self):
        return 'GET'

    def headers(self):
        return {
            'X-Seller-id': self.seller_id,
            'Host': config.INTERNAL_HOST_URLS[0]
        }

    def assert_attribute_set_content(self, res):
        self.assertEqual(self.attribute_set.id, res['id'])
        self.assertEqual(self.attribute_set.name, res['name'])
        self.assertEqual(self.attribute_set.code, res['code'])

    def test_getAttributeSetExisted__returnCorrectInfo(self):
        code, body = self.call_api()

        self.assertEqual(200, code)
        self.assert_attribute_set_content(body['result'])

    def test_passAttributeSetIdNull__returnNotFoundException(self):
        code, _ = self.call_api(url='/attribute_sets/null')

        self.assertEqual(404, code)

    def test_passAttributeSetIdNotExist__returnInvalidResponse(self):
        code, _ = self.call_api(url='/attribute_sets/696969696969')

        self.assertEqual(400, code)

    def test_UOMAttribute_SellerWithUomManagement_return200(self):
        seller_id = random.choice(config.SELLER_ONLY_UOM)
        self.setUOM(seller_id)
        self.seller_id = seller_id
        code, body = self.call_api()

        self.assertEqual(200, code)
        self.assert_attribute_set_content(body['result'])
        has_uom = 0
        for attribute in body['result']['attributes']:
            if attribute.get('code') == UOM_CODE_ATTRIBUTE:
                has_uom = has_uom + 1
                self.assertEqual(len(attribute.get('options')), 1)
        self.assertEqual(has_uom, 1)

    def test_UOMAttribute_SellerWithoutUomManagement_return200(self):
        seller_id = random.choice(config.SELLER_ONLY_UOM)
        self.setUOM(seller_id)
        self.seller_id = sum(config.SELLER_ONLY_UOM) + self.seller_id
        code, body = self.call_api()

        self.assertEqual(200, code)
        self.assert_attribute_set_content(body['result'])
        has_uom = 0
        for attribute in body['result']['attributes']:
            if attribute.get('code') == UOM_CODE_ATTRIBUTE:
                has_uom = has_uom + 1
                self.assertNotEqual(attribute.get('options'), [])

        self.assertEqual(has_uom, 1)

    def testNormalOption(self):
        new_attribute = random.choice(self.attributes)
        new_attribute.value_type = ATTRIBUTE_TYPE.SELECTION
        new_option = fake.attribute_option(attribute_id=new_attribute.id)
        code, body = self.call_api()

        self.assertEqual(200, code)
        self.assert_attribute_set_content(body['result'])
        has_check = 0
        for attribute in body['result']['attributes']:
            if attribute.get('code') == new_attribute.code:
                has_check = has_check + 1
                self.assertEqual(attribute.get('options')[-1].get('value'), new_option.value)
                self.assertEqual(attribute.get('options')[-1].get('code'), new_option.code)
                self.assertEqual(attribute.get('options')[-1].get('id'), new_option.id)

        self.assertEqual(has_check, 1)


class AttributeSetOptionsTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-956'
    FOLDER = '/AttributeSet/Get/Thumbnail'

    def setUp(self):
        super().setUp()
        self.seller_id = fake.integer()
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [
            fake.attribute_group(set_id=self.attribute_set.id, system_group=False)
            for _ in range(2)
        ]
        group_ids = [group.id for group in self.attribute_groups]
        self.attributes = [
            fake.attribute(group_ids=group_ids,
                           value_type=random.choice([
                               ATTRIBUTE_TYPE.SELECTION,
                               ATTRIBUTE_TYPE.MULTIPLE_SELECT
                           ]))
        ]

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}'

    def method(self):
        return 'GET'

    def __assert_attribute_option(self, option_obj, option_res):
        self.assertEqual(option_res.get('value'), option_obj.value)
        self.assertEqual(option_res.get('code'), option_obj.code)
        self.assertEqual(option_res.get('id'), option_obj.id)
        self.assertEqual(option_res.get('thumbnailUrl'), option_obj.thumbnail_url)

    def test_get_attribute_set_return200_with_thumbnail_url(self):
        new_attribute = random.choice(self.attributes)
        new_attribute.value_type = ATTRIBUTE_TYPE.SELECTION
        new_option = fake.attribute_option(attribute_id=new_attribute.id,
                                           thumbnail_url=f'https://teko.vn/{fake.text(100)}')
        code, body = self.call_api()

        self.assertEqual(200, code)
        for attribute in body['result']['attributes']:
            if attribute.get('code') == new_attribute.code:
                self.__assert_attribute_option(new_option, attribute.get('options')[-1])

    def test_get_attribute_set_return200_without_thumbnail_url(self):
        code, body = self.call_api()

        self.assertEqual(200, code)
        for attribute in body['result']['attributes']:
            for option in attribute.get('options'):
                self.assertIsNone(option.get('thumbnailUrl'))
