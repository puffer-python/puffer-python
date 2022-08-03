#coding=utf-8

import re
from tests.faker import fake
from tests.catalog.api import APITestCase
from catalog import (
    models,
    utils,
)
from catalog.services.products import ProductVariantService


variant_service = ProductVariantService.get_instance()

class CreateVariantServiceTestCase(APITestCase):
    ISSUE_KEY = 'SC-341'

    def setUp(self):
        self.iam_user = fake.iam_user()
        self.attribute_set = fake.attribute_set()
        self.group = fake.attribute_group(self.attribute_set.id)
        self.attributes = [fake.attribute(value_type='selection') for _ in range(5)]
        self.options = [fake.attribute_option(attribute.id) for attribute in self.attributes]
        self.attribute_group_attribute = [fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=True
        ) for attr in self.attributes]
        self.master_category = fake.master_category(
            is_active=True
        )

        self.attributes_data = list()
        for n_attribute in range(3):
            attr_grou_attr = fake.random_element(self.attribute_group_attribute)
            self.attributes_data.append({
                'id': attr_grou_attr.attribute_id,
                'value': attr_grou_attr.attribute.options[0].id
            })

    def test_passValidData__returnVariantAndListVariantAttribute(self):
        product = fake.product(master_category_id=self.master_category.id)
        variant, attributes = variant_service.create_variant(
            product.id, self.iam_user.email, self.attributes_data)
        attributes_map = dict()
        for attribute in attributes:
            attributes_map[attribute.attribute_id] = attribute
        assert variant.product_id == product.id
        assert len(self.attributes_data) == len(attributes)
        assert re.fullmatch(r'^[a-zA-Z0-9]{9,9}$', variant.code)

        # deep check
        opt_values = list()
        for attribute_data in self.attributes_data:
            assert attribute_data['id'] in attributes_map
            option = models.AttributeOption.query.get(attribute_data['value'])
            assert option.attribute_id == attributes_map[attribute_data['id']].attribute_id
            opt_values.append(option.value)
        assert variant.code
        assert f'{variant.product.name} ({", ".join(opt_values)})' == variant.name
        assert utils.generate_url_key(variant.name) == variant.url_key

    def test_passValidDataWithoutVariant__returnDefaultVariant(self):
        product = fake.product(master_category_id=self.master_category.id)
        variant, attributes = variant_service.create_variant(product.id, self.iam_user.email)
        assert variant
        assert len(attributes) == 0
        assert variant.name == variant.product.name

    def test_passValidData__productAssignedDefaultVariant(self):
        fake.attribute(code='uom_ratio', value_type='text')
        product = fake.product(master_category_id=self.master_category.id)
        variants = variant_service.create_variants(
            product.id, [{'attributes': self.attributes_data}], self.iam_user.email)
        assert product.default_variant.id == variants[0]['id']
        assert product.default_variant.name == variants[0]['name']
        assert product.default_variant.code == variants[0]['code']
