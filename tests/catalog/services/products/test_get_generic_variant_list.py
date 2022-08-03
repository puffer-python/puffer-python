#coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products import ProductVariantService


service = ProductVariantService.get_instance()


class GetListGenericVariantTestCase(APITestCase):
    ISSUE_KEY = 'SC-389'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.variants = [fake.product_variant(product_id=self.product.id, created_by=self.user.email)
                         for _ in range(5)]
        for variant in self.variants:
            fake.sellable_product(variant_id=variant.id)

    def assertVariantList(self, list1, list2):
        assert len(list1) == len(list2)
        list1_sorted = sorted(list1, key=lambda item: item.id)
        list2_sorted = sorted(list2, key=lambda item: item.id)
        for a, b in zip(list1_sorted, list2_sorted):
            assert a == b

    def test_passValidProductId__returnListVariant(self):
        filters = {
            'product_id': self.product.id,
        }
        page = 1
        page_size = 5
        by = None
        order = None
        ret, total_records = service.get_variants(filters, page, page_size, by, order)
        assert total_records == 5
        self.assertVariantList(ret, self.variants)

    def test_passGetPublishedVariatnOwnedByOtherUser__returnListVariant(self):
        other_user = fake.iam_user(seller_id=self.seller.id)
        variant = fake.product_variant(product_id=self.product.id, created_by=other_user.email, editing_status_code='approved')
        fake.sellable_product(variant_id=variant.id)
        filters = {
            'product_id': self.product.id
        }
        page = 1
        page_size = 10
        by = None
        order = None
        ret, total_records = service.get_variants(filters, page, page_size, by, order)
        assert total_records == 5 + 1
        self.assertVariantList(ret, self.variants + [variant])
