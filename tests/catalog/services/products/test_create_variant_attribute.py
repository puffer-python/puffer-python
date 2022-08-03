# coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products.variant import ProductVariantService
from catalog import models


class CreateVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'SC-377'

    def setUp(self):
        # setup database
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
        self.variant = fake.product_variant(self.product.id)


        # setup data param
        self.attributes_data = list()
        self.attributes_data.append({
            'id': self.attributes['system']['text'].id,
            'value': fake.text()
        })
        self.attributes_data.append({
            'id': self.attributes['system']['number'].id,
            'value': fake.random_number()
        })
        self.attributes_data.append({
            'id': self.attributes['system']['selection'].id,
            'value': fake.random_element(self.attributes['system']['selection'].options).id
        })
        self.attributes_data.append({
            'id': self.attributes['system']['multiple_select'].id,
            'value': list(map(
                lambda option: option.id,
                self.attributes['system']['multiple_select'].options,
            ))
        })
        self.attributes_data.append({
            'id': self.attributes['normal']['text'].id,
            'value': fake.text()
        })
        self.attributes_data.append({
            'id': self.attributes['normal']['number'].id,
            'value': fake.random_number()
        })
        self.attributes_data.append({
            'id': self.attributes['normal']['selection'].id,
            'value': fake.random_element(self.attributes['normal']['selection'].options).id
        })
        self.attributes_data.append({
            'id': self.attributes['normal']['multiple_select'].id,
            'value': list(map(
                lambda option: option.id,
                self.attributes['normal']['multiple_select'].options,
            ))
        })

    def assertVariantAttributeEqual(self):
        for attribute_data in self.attributes_data:
            variant_attribute = models.VariantAttribute.query.filter(
                models.VariantAttribute.attribute_id == attribute_data['id'],
                models.VariantAttribute.variant_id == self.variant.id
            ).first()
            assert variant_attribute
            value_type = variant_attribute.attribute.value_type
            if value_type == 'multiple_select':
                assert attribute_data['value'] == list(map(int, variant_attribute.value.split(',')))
            elif value_type in ('number', 'selection'):
                ftype = type(attribute_data['value'])
                assert attribute_data['value'] == ftype(variant_attribute.value)
            else: # value_type is text
                assert attribute_data['value'] == variant_attribute.value

    def test_passValidData__returnSuccess(self):
        service = ProductVariantService.get_instance()
        variant = service.upsert_variant_attributes(
            self.variant.id, self.attributes_data
        )
        self.assertVariantAttributeEqual()


    def test_passAttributeExisted__returnSuccess(self):
        models.db.session.add(models.VariantAttribute(
            variant_id=self.variant.id,
            attribute_id=self.attributes['normal']['text'].id,
            value=fake.text()
        ))
        service = ProductVariantService.get_instance()
        variant = service.upsert_variant_attributes(
            self.variant.id, self.attributes_data
        )
        self.assertVariantAttributeEqual()
