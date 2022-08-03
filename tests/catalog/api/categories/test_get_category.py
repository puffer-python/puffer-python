# coding=utf-8
from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user


class GetDetailCategoryTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1257'
    FOLDER = '/Category/getCategoryById'

    def url(self):
        return '/categories/{}'

    def method(self):
        return 'GET'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        self.attribute_groups = []
        self.attributes = []
        self.fake_attribute_set()
        self.fake_uom(self.attribute_set)
        self.category = fake.category(
            seller_id=self.seller.id, is_active=True,
            attribute_set_id=self.attribute_set.id
        )

    def fake_attribute_set(self, is_variation=1, **kwargs):
        self.attribute_set = fake.attribute_set(**kwargs)
        self.attribute_group = fake.attribute_group(set_id=self.attribute_set.id)
        self.attribute_groups.append(self.attribute_group)
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True,
                is_variation=is_variation
            ) for i in range(1, 3)
        ]
        self.attributes = attributes

        fake.attribute_group_attribute(attribute_id=attributes[0].id, group_ids=[self.attribute_group.id],
                                       is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=attributes[1].id, group_ids=[self.attribute_group.id],
                                       is_variation=is_variation)
        return self.attribute_set

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id)
        self.attribute_groups.append(uom_attribute_group)
        uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        fake.attribute_option(uom_attribute.id, value='Cái')
        fake.attribute_option(uom_attribute.id, value='Chiếc')
        self.attributes.append(uom_attribute)
        self.attributes.append(ratio_attribute)

    def assert_groups(self, data, expect):
        """
        data: body['result']['groups']
        expect: self.attribute_groups
        """
        data = sorted(data, key=lambda x: x.get('id'))
        expect = sorted(expect, key=lambda x: x.id)
        for i in range(len(data)):
            assert data[i].get('id') == expect[i].id
            assert data[i].get('name') == expect[i].name
            assert data[i].get('path') == expect[i].path
            assert data[i].get('level') == expect[i].level
            assert data[i].get('priority') == expect[i].priority
            assert data[i].get('parentId') == expect[i].parent_id
            assert data[i].get('isFlat') == expect[i].is_flat

    def assert_attributes(self, data, expect):
        """
        data: body['result']['attributes']
        expect: self.attributes
        """
        data = sorted(data, key=lambda x: x.get('id'))
        expect = sorted(expect, key=lambda x: x.id)
        for i in range(len(data)):
            attr_info = models.AttributeGroupAttribute.query.filter(
                models.AttributeGroupAttribute.attribute_id == data[i].get('id')
            ).first()
            assert data[i].get('id') == expect[i].id
            assert data[i].get('name') == expect[i].name
            assert data[i].get('code') == expect[i].code
            assert data[i].get('unitId') == expect[i].unit_id
            assert data[i].get('valueType') == expect[i].value_type
            assert data[i].get('description') == expect[i].description
            assert data[i].get('displayName') == expect[i].display_name
            assert data[i].get('isRequired') == expect[i].is_required
            assert data[i].get('isComparable') == expect[i].is_comparable
            assert data[i].get('isSearchable') == expect[i].is_searchable
            assert data[i].get('isFilterable') == expect[i].is_filterable
            assert data[i].get('isVariation') == bool(attr_info.is_variation)
            assert data[i].get('variationDisplayType') == attr_info.variation_display_type
            assert data[i].get('textBefore') == attr_info.text_before
            assert data[i].get('textAfter') == attr_info.text_after
            assert data[i].get('highlight') == attr_info.highlight
            assert data[i].get('priority') == attr_info.priority
            options = [option for option in expect[i].options if option.seller_id != 4]
            for j in range(len(data[i].get('options'))):
                assert data[i].get('options')[j].get('id') == options[j].id
                assert data[i].get('options')[j].get('value') == options[j].value
                assert data[i].get('options')[j].get('code') == options[j].code
                assert data[i].get('options')[j].get('thumbnailUrl') == options[j].thumbnail_url

    def test_getMappedMasterCategory_200_returnSuccessfully(self):
        self.category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))
            self.assertEqual(code, 200)

            self.assertTrue('masterCategory' in body['result'])
            assert body['result']['masterCategory']['id'] == self.master_category.id
            assert body['result']['masterCategory']['path'] == self.master_category.path

    def test_getUnMappedMasterCategory_200_returnCategory(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))
            self.assertEqual(code, 200)
            self.assertTrue('masterCategory' in body['result'])
            self.assertIsNone(body['result']['masterCategory'])

    def test__200__returnNoShippingType(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))
            self.assertEqual(code, 200)
            self.assertEqual(len(body['result']['shippingTypes']), 0)

    def test__200__returnOnlyOneShippingType(self):
        expect_shipping_type = fake.shipping_type()
        fake.category_shipping_type(self.category.id, expect_shipping_type.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))

            self.assertEqual(code, 200)

            result = body['result']
            self.assertEqual(len(result['shippingTypes']), 1)
            self.assertEqual(result['shippingTypes'][0]['id'], expect_shipping_type.id)
            self.assertEqual(result['shippingTypes'][0]['code'], expect_shipping_type.code)
            self.assertEqual(result['shippingTypes'][0]['name'], expect_shipping_type.name)

    def test__200__returnMultipleShippingTypes(self):
        expect_shipping_types = [fake.shipping_type() for _ in range(2)]
        for shipping_type in expect_shipping_types:
            fake.category_shipping_type(self.category.id, shipping_type.id)

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))

            self.assertEqual(code, 200)

            result = body['result']['shippingTypes']
            self.assertEqual(len(result), 2)
            for i in range(2):
                self.assertIn(result[i]['id'], [shipping_type.id for shipping_type in expect_shipping_types])

    def test_return200(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))
            self.assertEqual(code, 200)
            self.assertIn('hasProduct', body['result'])
            self.assert_groups(body['result']['groups'], self.attribute_groups)
            self.assert_attributes(body['result']['attributes'], self.attributes)

    def test_return200_getAttributeFromParentCategory(self):
        category = fake.category(
            seller_id=self.seller.id, is_active=True,
            attribute_set_id=None,
            parent_id=self.category.id
        )
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(category.id))
            self.assertEqual(code, 200)
            self.assert_groups(body['result']['groups'], self.attribute_groups)
            self.assert_attributes(body['result']['attributes'], self.attributes)

    def test_canNotFindAttribute_return400_attributeIsNone(self):
        self.category = fake.category(
            seller_id=self.seller.id, is_active=True,
        )
        self.category.attribute_set_id = None
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.url().format(self.category.id))
            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), 'Danh mục chưa có bộ thuộc tính')
