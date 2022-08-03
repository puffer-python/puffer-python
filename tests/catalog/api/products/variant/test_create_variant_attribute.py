# coding=utf-8
from unittest.mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user


class CreateVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'SC-377'

    def setUp(self):
        # setup database
        self.iam_user = fake.iam_user()
        self.attribute_set = fake.attribute_set()
        self.groups = {
            'normal': fake.attribute_group(
                set_id=self.attribute_set.id,
                system_group=False
            ),
            'system': fake.attribute_group(
                set_id=self.attribute_set.id,
                system_group=True
            )
        }
        self.attributes = {
            'system': {
                'text': fake.attribute(value_type='text'),
                'number': fake.attribute(value_type='number'),
                'selection': fake.attribute(value_type='selection'),
                'multiple_select': fake.attribute(value_type='multiple_select')
            },
            'normal': {
                'text': fake.attribute(value_type='text'),
                'number': fake.attribute(value_type='number'),
                'selection': fake.attribute(value_type='selection'),
                'multiple_select': fake.attribute(value_type='multiple_select')
            }
        }
        self.options = [fake.attribute_option(self.attributes['system']['selection'].id),
                        fake.attribute_option(self.attributes['normal']['selection'].id),
                        fake.attribute_option(self.attributes['system']['multiple_select'].id),
                        fake.attribute_option(self.attributes['system']['multiple_select'].id),
                        fake.attribute_option(self.attributes['normal']['multiple_select'].id),
                        fake.attribute_option(self.attributes['normal']['multiple_select'].id)]
        self.attribute_group_attribute = {
            'normal': [],
            'system': []
        }
        for attr in self.attributes['system'].values():
            self.attribute_group_attribute['system'].append(fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[self.groups['system'].id],
                is_variation=False
            ))
        for attr in self.attributes['normal'].values():
            self.attribute_group_attribute['normal'].append(fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[self.groups['normal'].id],
                is_variation=False
            ))
        self.master_category = fake.master_category(
            is_active=True
        )
        self.product = fake.product(
            master_category_id=self.master_category.id,
            attribute_set_id=self.attribute_set.id
        )
        # setup variants
        self.variation_attribute = fake.attribute(value_type='selection')
        self.variation_opts = [fake.attribute_option(self.variation_attribute.id),
                               fake.attribute_option(self.variation_attribute.id)]
        fake.attribute_group_attribute(
            attribute_id=self.variation_attribute.id,
            group_ids=[self.groups['normal'].id],
            is_variation=True
        )
        fake.attribute_group_attribute(
            attribute_id=self.variation_attribute.id,
            group_ids=[self.groups['normal'].id],
            is_variation=True
        )
        self.variants = [fake.product_variant(self.product.id, self.iam_user.email),
                         fake.product_variant(self.product.id, self.iam_user.email)]

        # setup request data
        self.data = {
            'variants': []
        }
        for variant in self.variants:
            attributes = []
            attributes.append({
                'id': self.attributes['system']['text'].id,
                'value': fake.text()
            })
            attributes.append({
                'id': self.attributes['system']['number'].id,
                'value': fake.random_number()
            })
            attributes.append({
                'id': self.attributes['system']['selection'].id,
                'value': fake.random_element(self.attributes['system']['selection'].options).id
            })
            attributes.append({
                'id': self.attributes['system']['multiple_select'].id,
                'value': list(map(
                    lambda option: option.id,
                    self.attributes['system']['multiple_select'].options,
                ))
            })
            attributes.append({
                'id': self.attributes['normal']['text'].id,
                'value': fake.text()
            })
            attributes.append({
                'id': self.attributes['normal']['number'].id,
                'value': fake.random_number()
            })
            attributes.append({
                'id': self.attributes['normal']['selection'].id,
                'value': fake.random_element(self.attributes['normal']['selection'].options).id
            })
            attributes.append({
                'id': self.attributes['normal']['multiple_select'].id,
                'value': list(map(
                    lambda option: option.id,
                    self.attributes['normal']['multiple_select'].options,
                ))
            })
            self.data['variants'].append({
                'id': variant.id,
                'attributes': attributes
            })

    def url(self):
        return '/variants/attributes?filled=true'

    def method(self):
        return 'POST'

    def test_passValidData__returnSuccess(self):
        with logged_in_user(self.iam_user):
            code, body = self.call_api(data=self.data)
            assert code == 200, body
            assert len(body['result']) == len(self.data['variants'])
            variant_data_expect = sorted(self.data['variants'],
                                         key=lambda variant_data: variant_data['id'])
            variant_data_real = sorted(body['result'],
                                       key=lambda variant_data: variant_data['id'])
            for expect, real in zip(variant_data_expect, variant_data_real):
                assert expect['id'], real['id']
                expect_attrs = sorted(expect['attributes'], key=lambda attr: attr['id'])
                real_attrs = sorted(real['attributes'], key=lambda attr: attr['id'])
                for attr_expect, attr_real in zip(expect_attrs, real_attrs):
                    assert attr_expect['id'] == attr_real['id']
                    assert attr_expect['value'] == attr_real['value']

    def test_passInValidData__returnFailure(self):
        self.data['variants'][0]['attributes'][0] = None
        code, body = self.call_api(data=self.data)
        assert code == 400, body

    @patch('catalog.services.seller.get_seller_by_id')
    def test_400_notExistSeller(self, get_mock_seller):
        get_mock_seller.return_value = {}
        with logged_in_user(self.iam_user):
            code, body = self.call_api(data=self.data)
            assert code == 400
            assert body['message'] == 'User không thuộc seller nào'


class UpdateVariantAttribute(APITestCase):
    ISSUE_KEY = 'CATALOGUE-556'
    FOLDER = '/Variant/Create'

    def url(self):
        return '/variants/attributes'

    def method(self):
        return 'POST'

    def setUp(self):
        self.iam_user = fake.iam_user()

        self.attribute_set = fake.attribute_set()
        self.attribute_group = fake.attribute_group(set_id=self.attribute_set.id, system_group=False)

        self.category = fake.category(is_active=1)
        self.master_category = fake.master_category(is_active=1)
        self.product = fake.product(category_id=self.category.id, master_category_id=self.master_category.id)
        self.variant = fake.product_variant(product_id=self.product.id)

        self.attribute_1 = fake.attribute(
            group_ids=[self.attribute_group.id], value_type='number', variant_id=self.variant.id)
        self.attribute_2 = fake.attribute(
            group_ids=[self.attribute_group.id], value_type='number', variant_id=self.variant.id)

        self.sellable = fake.sellable_product(
            variant_id=self.variant.id,
            editing_status_code='active',
            seller_id=self.iam_user.seller_id,
            attribute_set_id=self.attribute_set.id
        )

        self.data = {
            "variants": [
                {
                    'id': self.variant.id,
                    'attributes': [
                        {
                            'id': self.attribute_1.id,
                            'value': 123
                        },
                        {
                            'id': self.attribute_2.id,
                            'value': 456
                        }
                    ]
                }
            ]
        }

    def delete_attribute(self, attribute_id):
        models.AttributeGroupAttribute.query.filter(
            models.AttributeGroupAttribute.attribute_id == attribute_id
        ).delete(synchronize_session='fetch')
        models.db.session.flush()

    def test_200_deleteAttributeFromAttributeSet(self):
        self.delete_attribute(self.attribute_1.id)

        with logged_in_user(self.iam_user):
            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)

            variant_attribute_1 = models.VariantAttribute.query.filter(
                models.VariantAttribute.attribute_id == self.attribute_1.id
            ).first()
            self.assertEqual(variant_attribute_1.value, '123')

            variant_attribute_2 = models.VariantAttribute.query.filter(
                models.VariantAttribute.attribute_id == self.attribute_2.id
            ).first()
            self.assertEqual(variant_attribute_2.value, '456')
