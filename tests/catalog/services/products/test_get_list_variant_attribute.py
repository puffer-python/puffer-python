#coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products import ProductVariantService


service = ProductVariantService.get_instance()


class GetListVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'SC-390'

    def setUp(self):
        self.user = fake.iam_user()
        attribute_set = fake.attribute_set()
        group = fake.attribute_group(attribute_set.id)
        self.product = fake.product(attribute_set_id=attribute_set.id, editing_status_code='approved')
        self.variants = [fake.product_variant(product_id=self.product.id,
                                              created_by=self.user.email) for _ in range(3)]
        self.variant_ids = list(map(lambda x: x.id, self.variants))
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

    def assertListVariantAttribute(self, list1, list2):
        variant_sort_fn = lambda x: x['id']
        attr_sort_fn = lambda x: x.id
        sorted_list1 = sorted(list1, key=variant_sort_fn)
        sorted_list2 = sorted(list2, key=variant_sort_fn)
        for variant_1, variant_2 in zip(sorted_list1, sorted_list2):
            self.assertEqual(len(variant_1['attributes']) + 1, len(variant_2['attributes']))

    def run_service(self):
        return service.get_variant_attribute_list(self.variant_ids)

    def test_passVariantIdsValid__returnListVariantAttribute(self):
        ret = self.run_service()
        self.assertListVariantAttribute(self.variant_attributes, ret)

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
        ret = self.run_service()
        self.assertListVariantAttribute(self.variant_attributes, ret)
