# coding=utf-8

import pytest
from marshmallow import ValidationError

from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators.variant import GetListVariantAttributeListValidator
from catalog.api.product.variant import schema
from tests import logged_in_user


class GetListVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'SC-390'

    def setUp(self):
        self.user = fake.iam_user()
        attribute_set = fake.attribute_set()
        group = fake.attribute_group(attribute_set.id)
        self.product = fake.product(attribute_set_id=attribute_set.id, editing_status_code='approved')
        self.variants = [fake.product_variant(product_id=self.product.id,
                                              created_by=self.user.email) for _ in range(3)]
        self.attributes = [fake.attribute(group_ids=[group.id]) for _ in range(5)]
        self.variant_attributes = list()
        for variant in self.variants:
            variant_data = {
                'id': variant.id,
                'attributes': list()
            }
            for attr in self.attributes:
                variant_data['attributes'].append(
                    fake.variant_attribute(variant.id, attr.id)
                )
            self.variant_attributes.append(variant_data)
        self.params = dict()
        self.params['variantIds'] = ','.join(map(lambda x: str(x.id), self.variants))

    def assertListVariantAttribute(self, list1, list2):
        variant_sort_fn = lambda x: x['id']
        attr_sort_fn = lambda x: x.id
        sorted_list1 = sorted(list1, key=variant_sort_fn)
        sorted_list2 = sorted(list2, key=variant_sort_fn)
        for variant_1, variant_2 in zip(sorted_list1, sorted_list2):
            assert variant_1['id'] == variant_2['id']
            sorted_attr_1 = sorted(variant_1['attributes'], key=attr_sort_fn)
            sorted_attr_2 = sorted(variant_2['attributes'], key=attr_sort_fn)
            for attr_1, attr_2 in zip(sorted_attr_1, sorted_attr_2):
                assert attr_1 == attr_2

    def run_validator(self):
        with logged_in_user(self.user):
            params = schema.GetVariantAttributeListParam().load(self.params)
            GetListVariantAttributeListValidator.validate(params)

    def test_passVariantIdsValid__returnListVariantAttribute(self):
        self.run_validator()

    def test_passVariantIdsContainApprovedVariantOwnedByOtherUser__returnListVariantAttribute(self):
        other_user = fake.iam_user()
        variant = fake.product_variant(product_id=self.product.id,
                                       created_by=other_user.email,
                                       editing_status_code='approved')
        variant_data = {
            'id': variant.id,
            'attributes': list()
        }
        for attr in self.attributes:
            variant_data['attributes'].append(fake.variant_attribute(variant.id, attr.id))
        self.variant_attributes.append(variant_data)
        self.params['variantIds'] += f',{variant.id}'
        self.run_validator()

    def test_passVariantIdsContainDraftVariantOwnedByOtherUser__passValidator(self):
        other_user = fake.iam_user()
        variant = fake.product_variant(product_id=self.product.id,
                                       created_by=other_user.email,
                                       editing_status_code='draft')
        variant_data = {
            'id': variant.id,
            'attributes': list()
        }
        for attr in self.attributes:
            variant_data['attributes'].append(fake.variant_attribute(variant.id, attr.id))
        self.variant_attributes.append(variant_data)
        self.params['variantIds'] += f',{variant.id}'
        self.run_validator()

    def test_passVariantIdNotExist__raiseBadRequestException(self):
        self.params['variantIds'] += f',{fake.random_int(1000)}'
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại id của một biến thể không tồn tại'

    def test_notPassVariantIds__raiseValidationError(self):
        self.params= dict()
        with pytest.raises(ValidationError) as error_info:
            self.run_validator()
        assert error_info.value.messages == {'variantIds': ['Missing data for required field.']}
